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

| Task | Split | Revision | R2 blind solve | R1 spec review | R3 family review |
|---|---|---|---|---|---|
| T-02EC43 | train | `2cad991bf44f` | n/a — not in sample | n/a — not in sample | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-02FF9D | train | `7b2d93e56b11` | n/a — not in sample | n/a — not in sample | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
| T-0717A6 | train | `72575b653895` | n/a — not in sample | n/a — not in sample | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-1D6F14 | train | `e1742d6b53a1` | n/a — not in sample | n/a — not in sample | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-1F835F | train | `272cb4fdc09f` | n/a — not in sample | n/a — not in sample | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-201937 | train | `a76a90775028` | n/a — not in sample | n/a — not in sample | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-25DE39 | train | `34b0e2d23364` | n/a — not in sample | n/a — not in sample | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-2D6100 | train | `0dcd020f9211` | n/a — not in sample | n/a — not in sample | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-46FBCC | train | `2467575f112b` | n/a — not in sample | n/a — not in sample | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-4F837F | train | `896ac0e74693` | n/a — not in sample | n/a — not in sample | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-5B4B11 | train | `5f6aecb072b9` | n/a — not in sample | n/a — not in sample | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-5E2670 | train | `4426f0cd4cbf` | n/a — not in sample | n/a — not in sample | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-5E46C3 | train | `04ff0a7b16fc` | n/a — not in sample | n/a — not in sample | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-6698FA | train | `4492ecf99777` | n/a — not in sample | n/a — not in sample | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-6D1A65 | train | `ff083f952ec1` | n/a — not in sample | n/a — not in sample | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-80BC88 | train | `1c2dcbeaaa74` | n/a — not in sample | n/a — not in sample | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-852F31 | train | `7b383deaf78c` | n/a — not in sample | n/a — not in sample | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
| T-8979C8 | train | `c777d499754a` | n/a — not in sample | n/a — not in sample | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-8B3FCC | train | `a368fa23125b` | n/a — not in sample | n/a — not in sample | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-8E32C6 | train | `c3bdc315fe76` | n/a — not in sample | n/a — not in sample | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-A40DCC | train | `83c966eed6a7` | n/a — not in sample | n/a — not in sample | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-A42411 | train | `beccabb7d7fa` | n/a — not in sample | n/a — not in sample | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-A50BE6 | train | `782aa5c92c0b` | n/a — not in sample | n/a — not in sample | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-B97FAB | train | `b70c08666eed` | n/a — not in sample | n/a — not in sample | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-BE5CAB | train | `9e5f20a4e006` | n/a — not in sample | n/a — not in sample | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-C4C410 | train | `455ec225472c` | n/a — not in sample | n/a — not in sample | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-C94302 | train | `5e96461e3d72` | n/a — not in sample | n/a — not in sample | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-CFE072 | train | `7ea631caa544` | n/a — not in sample | n/a — not in sample | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-D27F95 | train | `7f5a92cca6e6` | n/a — not in sample | n/a — not in sample | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-D2DA12 | train | `69d362f13591` | n/a — not in sample | n/a — not in sample | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-E4FDD8 | train | `99c3f94154cf` | n/a — not in sample | n/a — not in sample | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-EFC9FB | train | `1256209e4b12` | n/a — not in sample | n/a — not in sample | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-F3AD7D | train | `0d6fc30a7388` | n/a — not in sample | n/a — not in sample | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-FA734A | train | `7d0a90e748d5` | n/a — not in sample | n/a — not in sample | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
| T-FA96B2 | train | `0234b0ab7a27` | n/a — not in sample | n/a — not in sample | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-FBECFF | train | `55f9e75e58a1` | n/a — not in sample | n/a — not in sample | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-0222C3 | dev | `16b7213f35a5` | [PASS](completed/T-0222C3/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-0222C3/r1-shahid-ahmed-2026-10-23.md) | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-71E1D2 | dev | `dc8945e4233c` | n/a — not in sample | n/a — not in sample | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-84D47B | dev | `2abf0eadc6b0` | n/a — not in sample | n/a — not in sample | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-8F0E1E | dev | `3eb1d38939da` | [PASS](completed/T-8F0E1E/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-8F0E1E/r1-shahid-ahmed-2026-10-23.md) | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-9362E5 | dev | `86dbe7a2fdfb` | n/a — not in sample | n/a — not in sample | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-A680BE | dev | `bc662b78d80b` | [PASS](completed/T-A680BE/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-A680BE/r1-shahid-ahmed-2026-10-23.md) | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-C45901 | dev | `70159daa421b` | n/a — not in sample | n/a — not in sample | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-CC052D | dev | `26e10d7f52b3` | n/a — not in sample | n/a — not in sample | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-D30567 | dev | `a3840def087b` | n/a — not in sample | n/a — not in sample | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-DC7A6B | dev | `cfe72afaef9a` | n/a — not in sample | n/a — not in sample | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-E72409 | dev | `59e0f1714713` | n/a — not in sample | n/a — not in sample | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-F88990 | dev | `6964b8ff6fe6` | n/a — not in sample | n/a — not in sample | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
| T-0A0D10 | test | `8bc1cd9818ac` | [PASS](completed/T-0A0D10/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-0A0D10/r1-shahid-ahmed-2026-10-23.md) | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-0A802E | test | `c1966f11f876` | n/a — not in sample | n/a — not in sample | [F06](completed/families/r3-F06-shahid-ahmed-2026-10-23.md) |
| T-0B0633 | test | `729c323eabd5` | [PASS](completed/T-0B0633/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-0B0633/r1-shahid-ahmed-2026-10-23.md) | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-107867 | test | `e2987afd195e` | n/a — not in sample | n/a — not in sample | [F10](completed/families/r3-F10-shahid-ahmed-2026-10-23.md) |
| T-11EA31 | test | `9e6201acbb2d` | [PASS](completed/T-11EA31/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-11EA31/r1-shahid-ahmed-2026-10-23.md) | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
| T-175EBC | test | `498975650d91` | n/a — not in sample | n/a — not in sample | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-1A3136 | test | `90627c206c5e` | [PASS](completed/T-1A3136/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-1A3136/r1-shahid-ahmed-2026-10-23.md) | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-202621 | test | `94a087469c22` | n/a — not in sample | n/a — not in sample | [F03](completed/families/r3-F03-shahid-ahmed-2026-10-23.md) |
| T-5B8D32 | test | `eb8a19a358b1` | [PASS](completed/T-5B8D32/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-5B8D32/r1-shahid-ahmed-2026-10-23.md) | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-5C4594 | test | `02338c88343f` | n/a — not in sample | n/a — not in sample | [F11](completed/families/r3-F11-shahid-ahmed-2026-10-23.md) |
| T-6BAF87 | test | `089ec602b9ff` | [PASS](completed/T-6BAF87/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-6BAF87/r1-shahid-ahmed-2026-10-23.md) | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-6C23E6 | test | `7b855b65ebd5` | [PASS](completed/T-6C23E6/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-6C23E6/r1-shahid-ahmed-2026-10-23.md) | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-6F7DAA | test | `87b5013a2768` | n/a — not in sample | n/a — not in sample | [F05](completed/families/r3-F05-shahid-ahmed-2026-10-23.md) |
| T-739D69 | test | `b3eff90a0c2c` | [PASS](completed/T-739D69/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-739D69/r1-shahid-ahmed-2026-10-23.md) | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-7E294F | test | `24a5fa198996` | n/a — not in sample | n/a — not in sample | [F08](completed/families/r3-F08-shahid-ahmed-2026-10-23.md) |
| T-89B109 | test | `9dac6af8fb2e` | [PASS](completed/T-89B109/r2-shahid-ahmed-2026-10-23.md) | [approve](completed/T-89B109/r1-shahid-ahmed-2026-10-23.md) | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-B2A72C | test | `2ffd99bda211` | n/a — not in sample | n/a — not in sample | [F02](completed/families/r3-F02-shahid-ahmed-2026-10-23.md) |
| T-BBE12C | test | `42835a15b420` | n/a — not in sample | n/a — not in sample | [F04](completed/families/r3-F04-shahid-ahmed-2026-10-23.md) |
| T-C07FE6 | test | `f21e76acfc84` | n/a — not in sample | n/a — not in sample | [F09](completed/families/r3-F09-shahid-ahmed-2026-10-23.md) |
| T-CB94BF | test | `c99f15d754f4` | n/a — not in sample | n/a — not in sample | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-CF549E | test | `57c0bb32c914` | n/a — not in sample | n/a — not in sample | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-E673B5 | test | `89264d2fe0f7` | n/a — not in sample | n/a — not in sample | [F01](completed/families/r3-F01-shahid-ahmed-2026-10-23.md) |
| T-F91D2D | test | `d5f39139593a` | n/a — not in sample | n/a — not in sample | [F07](completed/families/r3-F07-shahid-ahmed-2026-10-23.md) |
| T-FB1EDA | test | `52f1f20ca6ec` | n/a — not in sample | n/a — not in sample | [F12](completed/families/r3-F12-shahid-ahmed-2026-10-23.md) |
