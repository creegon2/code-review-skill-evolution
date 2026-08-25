# Third-party notices

This repository does not vendor third-party source code, benchmark data, model
outputs, or binary packages. The integrations below are external and optional.

## Microsoft SkillOpt

- Project: Microsoft SkillOpt
- Source: https://github.com/microsoft/SkillOpt
- License: MIT
- Public baseline used while validating this companion boundary:
  `3c8873f016397817dcd40c3e5436d92fe19372b8`
- Copyright: Copyright (c) 2026 Microsoft Corporation

The public core does not copy SkillOpt Trainer, reflection, merge, or gate
logic. Operators who enable the formal integration must obtain and retain the
upstream license with their checkout.

## Alibaba AACR-Bench

- Project: Alibaba AACR-Bench
- Source: https://github.com/alibaba/aacr-bench
- License: Apache License 2.0
- Reference commit for the original code-review scorer boundary:
  `b3072489eace26efca8bcf2b1ac6a24ba64f82c1`

AACR-Bench code and data are not included here. Its datasets can contain
material originating from additional projects; operators are responsible for
the corresponding access, attribution, and redistribution terms.

## HeavenBase

- Project: HeavenBase
- Public distribution metadata: https://pypi.org/project/heavenbase/
- License: MIT

HeavenBase is not a dependency of the public core. A detached audit-store
sidecar may be implemented by an operator as an optional integration; no
private wheel or local-path dependency is shipped in this repository.
