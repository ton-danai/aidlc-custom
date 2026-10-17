# Vendored: AWS AI-DLC rules v1.0.1

`aidlc-rules/` is the content of `ai-dlc-rules-v1.0.1.zip` from
https://github.com/awslabs/aidlc-workflows/releases/tag/v1.0.1
(zip sha256 `ac0601544b6c7ba41b541a7a96259d6ea3995ea0b94b2a58a333ae7898e22b39`),
unchanged except that `.markdownlint-cli2.yaml` is left out and the repository's
`LICENSE` (MIT-0) is added.

aidlc-custom targets the v1 rule layout. AI-DLC 2.x uses a different runtime and
is not supported. `tools/export_to_project.py --with-aidlc` installs these rules.
To update, replace `aidlc-rules/` with a newer 1.x zip and update this file.
