"""Generate the task suite: 12 worlds x 6 tasks = 72 tasks, split by world.

Assignment is fixed and documented:

* Worlds alternate between two family groups, so every world hosts six families and every
  family appears in six worlds: three train, one dev, two test.
* Within a family, instances take variants in the order [0, 1, 2, 2, 1, 0] following world
  order, so train sees every variant and dev/test mix outcomes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from invoiceops.domain.money import format_minor
from invoiceops.families.catalog import FAMILIES_BY_ID, VARIANTS_PER_FAMILY, f03_short_receipt
from invoiceops.tasks.model import Expectation, PrivateTask, PublicTask, TaskBundle
from invoiceops.worlds.builder import ScenarioBuilder, stable_seed
from invoiceops.worlds.companies import COMPANIES, CompanySpec

GROUP_A = ("F01", "F03", "F05", "F07", "F09", "F11")
GROUP_B = ("F02", "F04", "F06", "F08", "F10", "F12")
VARIANT_ORDER = (0, 1, 2, 2, 1, 0)
SLICE_WORLD = "w01-northstar"

PROMPT_TEMPLATE = """You are the accounts-payable assistant at {company}. Today's business date is \
{as_of}.

Invoice {invoice_id} from {vendor} ({total}) is in your queue. Investigate it and resolve it \
according to the company's accounts-payable policy, which is in the document store (search \
the documents collection for "policy"). Record your decision in the AP system using the \
tools, then finish with submit_case."""


def family_group(world_index: int) -> tuple[str, ...]:
    return GROUP_A if world_index % 2 == 0 else GROUP_B


def assignments() -> Iterator[tuple[CompanySpec, str, int]]:
    """Yield (company, family id, variant) for every task, in a fixed order."""
    seen: Counter[str] = Counter()
    for index, company in enumerate(COMPANIES):
        for family_id in family_group(index):
            instance = seen[family_id]
            seen[family_id] += 1
            yield company, family_id, VARIANT_ORDER[instance]


def task_id_for(world_id: str, family_id: str, variant: int, salt: str = "") -> str:
    digest = hashlib.sha256(f"{world_id}|{family_id}|{variant}|{salt}".encode()).hexdigest()
    return f"T-{digest[:6].upper()}"


def build_task(company: CompanySpec, family_id: str, variant: int, salt: str = "") -> TaskBundle:
    family = FAMILIES_BY_ID[family_id]
    if not 0 <= variant < VARIANTS_PER_FAMILY:
        raise ValueError(f"variant must be in [0, {VARIANTS_PER_FAMILY})")
    b = ScenarioBuilder(company, stable_seed(company.world_id, family_id, variant, salt))
    b.add_background(3)
    if family_id == "F03" and company.world_id == SLICE_WORLD and not salt:
        scenario = f03_short_receipt(b, variant, northstar_slice=True)
    else:
        scenario = family.build(b, variant)
    task_id = task_id_for(company.world_id, family_id, variant, salt)
    world = b.build([scenario.invoice.id], world_id=company.world_id)
    vendor = next(v for v in world.vendors if v.id == scenario.invoice.vendor_id)
    prompt = PROMPT_TEMPLATE.format(
        company=company.name,
        as_of=company.as_of,
        invoice_id=scenario.invoice.id,
        vendor=vendor.legal_name,
        total=format_minor(scenario.invoice.total_minor, world.company.currency),
    )
    public = PublicTask(task_id=task_id, prompt=prompt, world=world)
    private = PrivateTask(
        task_id=task_id,
        family=family.id,
        family_name=family.name,
        variant=variant,
        split=company.split,
        world_id=company.world_id,
        difficulty_hypothesis=scenario.difficulty,
        rationale=scenario.rationale,
        expectation=Expectation(invoice_id=scenario.invoice.id, outcomes=tuple(scenario.outcomes)),
        oracle_hint=scenario.hint,
    )
    return TaskBundle(public=public, private=private)


def build_suite() -> list[TaskBundle]:
    bundles = [build_task(c, f, v) for c, f, v in assignments()]
    ids = [b.public.task_id for b in bundles]
    if len(set(ids)) != len(ids):
        raise RuntimeError("task id collision")
    return bundles


def generated_training_variants(count: int, start: int = 0) -> Iterator[TaskBundle]:
    """Extra procedurally generated instances, drawn only from training worlds."""
    train = [c for c in COMPANIES if c.split == "train"]
    families = sorted(FAMILIES_BY_ID)
    for n in range(start, start + count):
        company = train[n % len(train)]
        family_id = families[(n // len(train)) % len(families)]
        variant = (n // (len(train) * len(families))) % VARIANTS_PER_FAMILY
        yield build_task(company, family_id, variant, salt=f"gen{n}")


def _dump(model_json: str) -> str:
    return json.dumps(json.loads(model_json), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_suite(root: Path) -> list[TaskBundle]:
    bundles = build_suite()
    for bundle in bundles:
        folder = root / bundle.private.split / bundle.public.task_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "public.json").write_text(_dump(bundle.public.model_dump_json()))
        (folder / "private.json").write_text(_dump(bundle.private.model_dump_json()))
    manifest = [
        {
            "task_id": b.public.task_id,
            "split": b.private.split,
            "world_id": b.private.world_id,
        }
        for b in bundles
    ]
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return bundles


def content_hash(bundle: TaskBundle) -> str:
    """Short revision hash of a task (public and private parts)."""
    payload = bundle.public.model_dump_json() + bundle.private.model_dump_json()
    return hashlib.sha256(payload.encode()).hexdigest()[:12]
