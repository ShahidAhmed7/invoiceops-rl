"""Twelve fictional companies. Every name, vendor, and product here is invented.

Splits are assigned per company before any task is generated, so a company's vendors,
products, and documents never appear in more than one split.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from invoiceops.domain.records import PartialInvoiceRule

Split = Literal["train", "dev", "test"]


@dataclass(frozen=True)
class VendorSpec:
    key: str
    legal_name: str
    email_domain: str


@dataclass(frozen=True)
class ItemSpec:
    sku: str
    description: str
    unit_price_minor: int


@dataclass(frozen=True)
class CompanySpec:
    world_id: str
    name: str
    split: Split
    as_of: str
    id_prefix: str
    departments: tuple[str, ...]
    price_tolerance_bps: int
    price_tolerance_cap_minor: int
    partial_invoice_rule: PartialInvoiceRule
    self_approval_limit_minor: int
    manager_limit_minor: int
    controller_limit_minor: int
    cfo_limit_minor: int
    vendors: tuple[VendorSpec, ...]
    items: tuple[ItemSpec, ...]


REQ = PartialInvoiceRule.REQUIRE_CORRECTED_INVOICE
PAY = PartialInvoiceRule.PAY_RECEIVED_PORTION


def _v(key: str, name: str, domain: str) -> VendorSpec:
    return VendorSpec(key=key, legal_name=name, email_domain=domain)


def _i(sku: str, description: str, price_minor: int) -> ItemSpec:
    return ItemSpec(sku=sku, description=description, unit_price_minor=price_minor)


COMPANIES: tuple[CompanySpec, ...] = (
    CompanySpec(
        world_id="w01-northstar",
        name="Northstar Components",
        split="train",
        as_of="2026-03-16",
        id_prefix="NS",
        departments=("Assembly", "Field Service", "Facilities"),
        price_tolerance_bps=200,
        price_tolerance_cap_minor=50_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=2_500_000,
        manager_limit_minor=5_000_000,
        controller_limit_minor=25_000_000,
        cfo_limit_minor=200_000_000,
        vendors=(
            _v("a", "Ferrovane Controls Ltd", "ferrovane.example"),
            _v("b", "Quellmark Cable Works", "quellmark.example"),
            _v("c", "Dunmore Fastener Supply", "dunmore-fastener.example"),
            _v("d", "Lattice Peak Enclosures", "latticepeak.example"),
        ),
        items=(
            _i("NS-CTL-120", "Motor controller unit, 24V", 12_000),
            _i("NS-CBL-018", "Shielded control cable, 50 m reel", 18_450),
            _i("NS-FST-440", "Stainless hex bolt kit, M8 (box of 200)", 6_275),
            _i("NS-ENC-300", "IP66 steel enclosure, 300 mm", 21_990),
            _i("NS-SNS-075", "Inductive proximity sensor", 7_540),
        ),
    ),
    CompanySpec(
        world_id="w02-bramblewood",
        name="Bramblewood Provisions",
        split="train",
        as_of="2026-04-09",
        id_prefix="BW",
        departments=("Kitchens", "Catering", "Stores"),
        price_tolerance_bps=300,
        price_tolerance_cap_minor=25_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=1_000_000,
        manager_limit_minor=3_000_000,
        controller_limit_minor=15_000_000,
        cfo_limit_minor=100_000_000,
        vendors=(
            _v("a", "Harrowgate Dairy Cooperative", "harrowgate-dairy.example"),
            _v("b", "Pinecrest Dry Goods", "pinecrest-dry.example"),
            _v("c", "Silvermoss Produce Traders", "silvermoss.example"),
            _v("d", "Coldwater Kitchen Equipment", "coldwater-kitchen.example"),
        ),
        items=(
            _i("BW-DRY-210", "Durum semolina, 25 kg sack", 4_890),
            _i("BW-DAI-033", "Cultured butter, 10 kg case", 11_200),
            _i("BW-EQP-901", "Combi oven door gasket", 17_850),
            _i("BW-PRD-517", "Mixed root vegetables, 20 kg crate", 3_640),
            _i("BW-PKG-064", "Compostable meal tray (case of 500)", 9_975),
        ),
    ),
    CompanySpec(
        world_id="w03-calderline",
        name="Calderline Marine Supply",
        split="train",
        as_of="2026-02-23",
        id_prefix="CL",
        departments=("Chandlery", "Rigging", "Workshop"),
        price_tolerance_bps=150,
        price_tolerance_cap_minor=40_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=2_000_000,
        manager_limit_minor=6_000_000,
        controller_limit_minor=30_000_000,
        cfo_limit_minor=150_000_000,
        vendors=(
            _v("a", "Brinehollow Rope Company", "brinehollow.example"),
            _v("b", "Saltmere Coatings", "saltmere.example"),
            _v("c", "Tidewrack Hardware", "tidewrack.example"),
            _v("d", "Gullstone Electronics", "gullstone.example"),
        ),
        items=(
            _i("CL-RPE-012", "Braided polyester line, 12 mm x 100 m", 26_400),
            _i("CL-PNT-205", "Antifouling paint, 5 L", 15_825),
            _i("CL-HDW-318", "Bronze cleat, 200 mm", 4_310),
            _i("CL-ELC-440", "Bilge pump switch assembly", 8_960),
            _i("CL-SFT-091", "Inflatable life jacket, 150N", 11_750),
        ),
    ),
    CompanySpec(
        world_id="w04-quillfeather",
        name="Quillfeather Office Systems",
        split="train",
        as_of="2026-05-04",
        id_prefix="QF",
        departments=("Workplace", "IT Services", "Print Room"),
        price_tolerance_bps=100,
        price_tolerance_cap_minor=20_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=1_500_000,
        manager_limit_minor=4_000_000,
        controller_limit_minor=20_000_000,
        cfo_limit_minor=120_000_000,
        vendors=(
            _v("a", "Arbelle Furniture Makers", "arbelle-furniture.example"),
            _v("b", "Kindlewick Paper Mills", "kindlewick.example"),
            _v("c", "Northwold Device Leasing", "northwold-devices.example"),
            _v("d", "Tessary Toner Supply", "tessary.example"),
        ),
        items=(
            _i("QF-CHR-450", "Task chair, mesh back", 18_900),
            _i("QF-PPR-080", "A4 copy paper, 80 gsm (box of 5 reams)", 2_745),
            _i("QF-DCK-220", "USB-C docking station", 14_380),
            _i("QF-TNR-610", "Toner cartridge, black, high yield", 9_120),
            _i("QF-DSK-160", "Sit-stand desk frame", 32_500),
        ),
    ),
    CompanySpec(
        world_id="w05-redfern",
        name="Redfern Hollow Instruments",
        split="train",
        as_of="2026-01-28",
        id_prefix="RH",
        departments=("Calibration", "Research", "Quality"),
        price_tolerance_bps=250,
        price_tolerance_cap_minor=60_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=3_000_000,
        manager_limit_minor=8_000_000,
        controller_limit_minor=40_000_000,
        cfo_limit_minor=250_000_000,
        vendors=(
            _v("a", "Mistral Ridge Optics", "mistralridge-optics.example"),
            _v("b", "Corrigan Fen Glassworks", "corriganfen.example"),
            _v("c", "Holloway Brook Metrology", "hollowaybrook.example"),
            _v("d", "Pellanor Reagents", "pellanor.example"),
        ),
        items=(
            _i("RH-OPT-055", "Precision lens assembly, 55 mm", 46_200),
            _i("RH-GLS-125", "Borosilicate beaker set", 5_890),
            _i("RH-CAL-700", "Reference weight set, class E2", 71_500),
            _i("RH-RGT-014", "Buffer solution pH 7.00, 1 L", 2_380),
            _i("RH-PRB-390", "Thermocouple probe, type K", 6_715),
        ),
    ),
    CompanySpec(
        world_id="w06-tamsin",
        name="Tamsin Ridge Hospitality",
        split="train",
        as_of="2026-06-12",
        id_prefix="TR",
        departments=("Housekeeping", "Front Office", "Spa"),
        price_tolerance_bps=500,
        price_tolerance_cap_minor=30_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=800_000,
        manager_limit_minor=2_500_000,
        controller_limit_minor=12_000_000,
        cfo_limit_minor=90_000_000,
        vendors=(
            _v("a", "Wrenfield Linen Services", "wrenfield-linen.example"),
            _v("b", "Amberlode Amenities", "amberlode.example"),
            _v("c", "Fairhollow Cleaning Supply", "fairhollow-clean.example"),
            _v("d", "Brightmere Lighting", "brightmere.example"),
        ),
        items=(
            _i("TR-LIN-240", "King bed sheet set, 300 thread count", 6_480),
            _i("TR-AMN-012", "Guest amenity kit (case of 100)", 15_300),
            _i("TR-CLN-505", "Concentrated floor cleaner, 5 L", 2_195),
            _i("TR-LGT-088", "LED lamp, warm white (pack of 10)", 4_650),
            _i("TR-TWL-130", "Bath towel, 600 gsm", 1_985),
        ),
    ),
    CompanySpec(
        world_id="w07-velloran",
        name="Velloran Medical Supplies",
        split="dev",
        as_of="2026-03-30",
        id_prefix="VM",
        departments=("Wards", "Theatre", "Pharmacy"),
        price_tolerance_bps=200,
        price_tolerance_cap_minor=35_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=1_200_000,
        manager_limit_minor=5_000_000,
        controller_limit_minor=20_000_000,
        cfo_limit_minor=150_000_000,
        vendors=(
            _v("a", "Orvanne Surgical", "orvanne-surgical.example"),
            _v("b", "Kestwick Sterile Goods", "kestwick.example"),
            _v("c", "Lumenhaven Diagnostics", "lumenhaven.example"),
            _v("d", "Bellcroft Medical Textiles", "bellcroft-textiles.example"),
        ),
        items=(
            _i("VM-SRG-210", "Single-use scalpel, No. 10 (box of 50)", 3_420),
            _i("VM-STR-044", "Sterile drape pack", 7_860),
            _i("VM-DGN-610", "Rapid test cassette (kit of 25)", 12_975),
            _i("VM-TXT-118", "Patient gown, reusable", 2_240),
            _i("VM-GLV-305", "Nitrile exam gloves (case of 1,000)", 8_590),
        ),
    ),
    CompanySpec(
        world_id="w08-hearthmoor",
        name="Hearthmoor Building Materials",
        split="dev",
        as_of="2026-07-21",
        id_prefix="HM",
        departments=("Yard", "Joinery", "Site Projects"),
        price_tolerance_bps=300,
        price_tolerance_cap_minor=75_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=2_000_000,
        manager_limit_minor=7_500_000,
        controller_limit_minor=35_000_000,
        cfo_limit_minor=200_000_000,
        vendors=(
            _v("a", "Grimsworth Timber Merchants", "grimsworth-timber.example"),
            _v("b", "Ollerby Aggregates", "ollerby.example"),
            _v("c", "Stanwell Moor Ironmongery", "stanwellmoor.example"),
            _v("d", "Coppice End Insulation", "coppiceend.example"),
        ),
        items=(
            _i("HM-TMB-450", "Kiln-dried softwood, 47 x 150 mm x 4.8 m", 1_895),
            _i("HM-AGG-020", "Crushed aggregate, 20 mm (bulk bag)", 6_150),
            _i("HM-IRN-330", "Heavy-duty hinge, galvanised (pair)", 2_760),
            _i("HM-INS-100", "Mineral wool slab, 100 mm (pack)", 4_480),
            _i("HM-PLB-125", "Plasterboard, 12.5 mm x 2.4 m", 1_120),
        ),
    ),
    CompanySpec(
        world_id="w09-glimmerdale",
        name="Glimmerdale Labware",
        split="test",
        as_of="2026-02-11",
        id_prefix="GL",
        departments=("Sample Prep", "Analytics", "Stores"),
        price_tolerance_bps=150,
        price_tolerance_cap_minor=45_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=1_800_000,
        manager_limit_minor=6_000_000,
        controller_limit_minor=25_000_000,
        cfo_limit_minor=180_000_000,
        vendors=(
            _v("a", "Thornhaugh Scientific", "thornhaugh-sci.example"),
            _v("b", "Varrick Cryogenics", "varrick-cryo.example"),
            _v("c", "Elmsfold Pipette Works", "elmsfold.example"),
            _v("d", "Quarrington Filtration", "quarrington.example"),
        ),
        items=(
            _i("GL-PIP-200", "Adjustable pipette, 20-200 uL", 21_400),
            _i("GL-CRY-050", "Cryogenic vial rack, 50 place", 3_860),
            _i("GL-TIP-960", "Filter tips, 200 uL (rack of 960)", 6_725),
            _i("GL-FLT-045", "Syringe filter 0.45 um (pack of 100)", 9_310),
            _i("GL-CEN-015", "Centrifuge tube, 15 mL (case of 500)", 5_480),
        ),
    ),
    CompanySpec(
        world_id="w10-juniperfold",
        name="Juniper Fold Logistics",
        split="test",
        as_of="2026-08-05",
        id_prefix="JF",
        departments=("Warehouse", "Fleet", "Dispatch"),
        price_tolerance_bps=250,
        price_tolerance_cap_minor=50_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=2_500_000,
        manager_limit_minor=7_000_000,
        controller_limit_minor=30_000_000,
        cfo_limit_minor=220_000_000,
        vendors=(
            _v("a", "Cradlebrook Pallet Company", "cradlebrook.example"),
            _v("b", "Ironvale Tyre Services", "ironvale-tyres.example"),
            _v("c", "Swiftmarsh Packaging", "swiftmarsh.example"),
            _v("d", "Halberd Lane Telematics", "halberdlane.example"),
        ),
        items=(
            _i("JF-PAL-120", "Heat-treated wooden pallet, 1200 x 1000", 1_765),
            _i("JF-TYR-225", "Truck tyre, 315/80 R22.5", 41_900),
            _i("JF-PKG-700", "Stretch wrap, 500 mm x 300 m", 2_390),
            _i("JF-TEL-010", "Vehicle telematics unit", 23_650),
            _i("JF-STR-330", "Ratchet strap, 10 m (pack of 4)", 3_175),
        ),
    ),
    CompanySpec(
        world_id="w11-pellucid",
        name="Pellucid Print Works",
        split="test",
        as_of="2026-04-27",
        id_prefix="PP",
        departments=("Pressroom", "Finishing", "Design Studio"),
        price_tolerance_bps=100,
        price_tolerance_cap_minor=15_000,
        partial_invoice_rule=PAY,
        self_approval_limit_minor=1_000_000,
        manager_limit_minor=4_500_000,
        controller_limit_minor=18_000_000,
        cfo_limit_minor=110_000_000,
        vendors=(
            _v("a", "Gossamer Ink Laboratories", "gossamer-ink.example"),
            _v("b", "Burnet Hill Paper Merchants", "burnethill.example"),
            _v("c", "Catchpole Plate Systems", "catchpole-plates.example"),
            _v("d", "Wyvernbrook Bindery Supply", "wyvernbrook.example"),
        ),
        items=(
            _i("PP-INK-050", "Process cyan ink, 2.5 kg tin", 8_640),
            _i("PP-PPR-135", "Silk coated paper, 135 gsm (pallet)", 61_200),
            _i("PP-PLT-404", "Thermal printing plate (box of 50)", 19_850),
            _i("PP-BND-220", "PUR binding adhesive, 20 kg", 14_270),
            _i("PP-BLD-016", "Guillotine blade, 1150 mm", 23_980),
        ),
    ),
    CompanySpec(
        world_id="w12-marrowind",
        name="Marrowind Energy Services",
        split="test",
        as_of="2026-09-14",
        id_prefix="ME",
        departments=("Field Operations", "Maintenance", "Safety"),
        price_tolerance_bps=200,
        price_tolerance_cap_minor=80_000,
        partial_invoice_rule=REQ,
        self_approval_limit_minor=3_500_000,
        manager_limit_minor=9_000_000,
        controller_limit_minor=45_000_000,
        cfo_limit_minor=300_000_000,
        vendors=(
            _v("a", "Fellgate Valve Engineering", "fellgate-valves.example"),
            _v("b", "Ramsden Scar Safety Wear", "ramsdenscar.example"),
            _v("c", "Trevannick Pump Hire", "trevannick.example"),
            _v("d", "Oxlade Instrumentation", "oxlade.example"),
        ),
        items=(
            _i("ME-VLV-080", "Ball valve, 80 mm, flanged", 38_600),
            _i("ME-PPE-210", "Flame-resistant coverall", 9_475),
            _i("ME-PMP-500", "Diaphragm pump service kit", 27_340),
            _i("ME-GAS-004", "Four-gas detector", 54_900),
            _i("ME-GSK-150", "Spiral wound gasket, 150 mm", 1_830),
        ),
    ),
)

COMPANIES_BY_ID: dict[str, CompanySpec] = {c.world_id: c for c in COMPANIES}


def companies_in(split: Split) -> tuple[CompanySpec, ...]:
    return tuple(c for c in COMPANIES if c.split == split)
