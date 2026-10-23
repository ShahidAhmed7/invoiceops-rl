# Review status

One row per task. `Revision` is the task's content hash (also shown by `invoiceops show-task`).
When a task changes, its revision changes and any earlier review of it no longer applies.

Implementation commit under review: `7066a8a901b0e7f6470ceac636165f38c235028c` (2026-10-23).

**Blocking findings (unresolved):** verifier escapes B1 (withdrawn proposals
invisible on payable outcomes) and B2 (clarification content unchecked) — see
`completed/attack-log.md`. Family-design weakness: F06 solved by a fixed habit —
see `completed/families/r3-F06-shahid-ahmed-2026-10-23.md`. **GPU phases: NOT approved.**
Signoff: `signoff/pre-gpu.md` (not approved).

Family reviews (R3, six instances each): `completed/families/r3-FXX-shahid-ahmed-2026-10-23.md`
for F01–F12. Other review artifacts: `completed/attack-log.md`,
`completed/mutation-assessment.md`, `completed/visibility-audit.md`,
`completed/prompt-v2-review.md`, `completed/mutations.md`,
`completed/spec-crosscheck.md`, `completed/attacks/` (14 scripted attacks +
12 family shortcut probes).

| Task | Split | Revision | R2 blind solve | R1 spec review |
|---|---|---|---|---|
| T-02EC43 | train | `2cad991bf44f` | not done | not done |
| T-02FF9D | train | `7b2d93e56b11` | not done | not done |
| T-0717A6 | train | `72575b653895` | not done | not done |
| T-1D6F14 | train | `e1742d6b53a1` | not done | not done |
| T-1F835F | train | `272cb4fdc09f` | not done | not done |
| T-201937 | train | `a76a90775028` | not done | not done |
| T-25DE39 | train | `34b0e2d23364` | not done | not done |
| T-2D6100 | train | `0dcd020f9211` | not done | not done |
| T-46FBCC | train | `2467575f112b` | not done | not done |
| T-4F837F | train | `896ac0e74693` | not done | not done |
| T-5B4B11 | train | `5f6aecb072b9` | not done | not done |
| T-5E2670 | train | `4426f0cd4cbf` | not done | not done |
| T-5E46C3 | train | `04ff0a7b16fc` | not done | not done |
| T-6698FA | train | `4492ecf99777` | not done | not done |
| T-6D1A65 | train | `ff083f952ec1` | not done | not done |
| T-80BC88 | train | `1c2dcbeaaa74` | not done | not done |
| T-852F31 | train | `7b383deaf78c` | not done | not done |
| T-8979C8 | train | `c777d499754a` | not done | not done |
| T-8B3FCC | train | `a368fa23125b` | not done | not done |
| T-8E32C6 | train | `c3bdc315fe76` | not done | not done |
| T-A40DCC | train | `83c966eed6a7` | not done | not done |
| T-A42411 | train | `beccabb7d7fa` | not done | not done |
| T-A50BE6 | train | `782aa5c92c0b` | not done | not done |
| T-B97FAB | train | `b70c08666eed` | not done | not done |
| T-BE5CAB | train | `9e5f20a4e006` | not done | not done |
| T-C4C410 | train | `455ec225472c` | not done | not done |
| T-C94302 | train | `5e96461e3d72` | not done | not done |
| T-CFE072 | train | `7ea631caa544` | not done | not done |
| T-D27F95 | train | `7f5a92cca6e6` | not done | not done |
| T-D2DA12 | train | `69d362f13591` | not done | not done |
| T-E4FDD8 | train | `99c3f94154cf` | not done | not done |
| T-EFC9FB | train | `1256209e4b12` | not done | not done |
| T-F3AD7D | train | `0d6fc30a7388` | not done | not done |
| T-FA734A | train | `7d0a90e748d5` | not done | not done |
| T-FA96B2 | train | `0234b0ab7a27` | not done | not done |
| T-FBECFF | train | `55f9e75e58a1` | not done | not done |
| T-0222C3 | dev | `16b7213f35a5` | [PASS](completed/T-0222C3/r2-cx-2026-10-23.md) | [approve](completed/T-0222C3/r1-shahid-ahmed-2026-10-23.md) |
| T-71E1D2 | dev | `dc8945e4233c` | not done | not done |
| T-84D47B | dev | `2abf0eadc6b0` | not done | not done |
| T-8F0E1E | dev | `3eb1d38939da` | [PASS](completed/T-8F0E1E/r2-cx-2026-10-23.md) | [approve](completed/T-8F0E1E/r1-shahid-ahmed-2026-10-23.md) |
| T-9362E5 | dev | `86dbe7a2fdfb` | not done | not done |
| T-A680BE | dev | `bc662b78d80b` | [PASS](completed/T-A680BE/r2-cx-2026-10-23.md) | [approve](completed/T-A680BE/r1-shahid-ahmed-2026-10-23.md) |
| T-C45901 | dev | `70159daa421b` | not done | not done |
| T-CC052D | dev | `26e10d7f52b3` | not done | not done |
| T-D30567 | dev | `a3840def087b` | not done | not done |
| T-DC7A6B | dev | `cfe72afaef9a` | not done | not done |
| T-E72409 | dev | `59e0f1714713` | not done | not done |
| T-F88990 | dev | `6964b8ff6fe6` | not done | not done |
| T-0A0D10 | test | `8bc1cd9818ac` | [PASS](completed/T-0A0D10/r2-cx-2026-10-23.md) | [approve](completed/T-0A0D10/r1-shahid-ahmed-2026-10-23.md) |
| T-0A802E | test | `c1966f11f876` | not done | not done |
| T-0B0633 | test | `729c323eabd5` | [PASS](completed/T-0B0633/r2-cx-2026-10-23.md) | [approve](completed/T-0B0633/r1-shahid-ahmed-2026-10-23.md) |
| T-107867 | test | `e2987afd195e` | not done | not done |
| T-11EA31 | test | `9e6201acbb2d` | [PASS](completed/T-11EA31/r2-cx-2026-10-23.md) | [approve](completed/T-11EA31/r1-shahid-ahmed-2026-10-23.md) |
| T-175EBC | test | `498975650d91` | not done | not done |
| T-1A3136 | test | `90627c206c5e` | [PASS](completed/T-1A3136/r2-cx-2026-10-23.md) | [approve](completed/T-1A3136/r1-shahid-ahmed-2026-10-23.md) |
| T-202621 | test | `94a087469c22` | not done | not done |
| T-5B8D32 | test | `eb8a19a358b1` | [PASS](completed/T-5B8D32/r2-cx-2026-10-23.md) | [approve](completed/T-5B8D32/r1-shahid-ahmed-2026-10-23.md) |
| T-5C4594 | test | `02338c88343f` | not done | not done |
| T-6BAF87 | test | `089ec602b9ff` | [PASS](completed/T-6BAF87/r2-cx-2026-10-23.md) | [approve](completed/T-6BAF87/r1-shahid-ahmed-2026-10-23.md) |
| T-6C23E6 | test | `7b855b65ebd5` | [PASS](completed/T-6C23E6/r2-cx-2026-10-23.md) | [approve](completed/T-6C23E6/r1-shahid-ahmed-2026-10-23.md) |
| T-6F7DAA | test | `87b5013a2768` | not done | not done |
| T-739D69 | test | `b3eff90a0c2c` | [PASS](completed/T-739D69/r2-cx-2026-10-23.md) | [approve](completed/T-739D69/r1-shahid-ahmed-2026-10-23.md) |
| T-7E294F | test | `24a5fa198996` | not done | not done |
| T-89B109 | test | `9dac6af8fb2e` | [PASS](completed/T-89B109/r2-cx-2026-10-23.md) | [approve](completed/T-89B109/r1-shahid-ahmed-2026-10-23.md) |
| T-B2A72C | test | `2ffd99bda211` | not done | not done |
| T-BBE12C | test | `42835a15b420` | not done | not done |
| T-C07FE6 | test | `f21e76acfc84` | not done | not done |
| T-CB94BF | test | `c99f15d754f4` | not done | not done |
| T-CF549E | test | `57c0bb32c914` | not done | not done |
| T-E673B5 | test | `89264d2fe0f7` | not done | not done |
| T-F91D2D | test | `d5f39139593a` | not done | not done |
| T-FB1EDA | test | `52f1f20ca6ec` | not done | not done |
