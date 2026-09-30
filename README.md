# SynapShare releases

Official downloads of [SynapShare](https://synapshare-16ced.web.app), a
software KVM and file-sharing app for Windows, macOS, Linux and Android.

**[Download the latest release](https://github.com/junrobo/synapshare-releases/releases/latest)**

| Platform | File |
|---|---|
| Windows 10 / 11 (64-bit) | `SynapShare-<version>-Setup.exe`, or the portable `.zip` |
| macOS (Apple Silicon) | `SynapShare-<version>-macos.dmg` |
| Linux x86_64 / aarch64 | `SynapShare-<version>-<arch>.flatpak` + `install-synapshare.sh` |
| Android 8.0+ | `SynapShare-<version>-android.apk` |

Found a bug? [Open an issue](https://github.com/junrobo/synapshare-releases/issues).

## Verifying a download

Every release carries `SHA256SUMS`, and every package has a GitHub build
provenance attestation proving it was built by this repository's release
workflow:

```sh
sha256sum -c SHA256SUMS --ignore-missing
gh attestation verify SynapShare-<version>-Setup.exe -R junrobo/synapshare-releases
```

## License

SynapShare is proprietary software ([LICENSE](LICENSE)); this repository
holds its release packages only. The packages include open-source components
under their own licenses, listed in `THIRD_PARTY_NOTICES.md` inside each
package. The source of the GPL/LGPL components (Deskflow, libportal) for
every release is published in
[junrobo/synapshare-oss](https://github.com/junrobo/synapshare-oss).

## Maintainers: how releases are built

`.github/workflows/release.yml` builds a release from the private source
repository and uploads it here as a draft; nothing is public until the
`publish` input is set and the source check passes.

1. In the source repository, bump the version and tag it (`v<version>`).
2. Publish the matching open-source release: in synapshare-oss run
   `scripts/make_source_release.sh <version>` (add the Deskflow commit of the
   Windows/macOS binaries, shown in the draft's `deskflow-manifest-*.json`),
   tag `synapshare-v<version>` and upload `dist/<version>/*`.
3. Run the workflow: `gh workflow run release.yml -R junrobo/synapshare-releases -f version=<version> -f publish=true`,
   then approve the `release` environment when asked.

One-time setup:

- **Environment** `release` (Settings → Environments) with *Required
  reviewers* set to the maintainer and deployments limited to `main`. Every
  secret below is an environment secret there, never a repository secret.
- **Secrets**
  - `SYNAPSHARE_DEPLOY_KEY`: private half of a read-only deploy key added to
    the source repository (Settings → Deploy keys, write access off).
  - `MACOS_CERTIFICATE_P12_BASE64`, `MACOS_CERTIFICATE_PASSWORD`,
    `MACOS_KEYCHAIN_PASSWORD`, `MACOS_SIGN_IDENTITY`, `APPLE_ID`,
    `APPLE_TEAM_ID`, `APPLE_APP_SPECIFIC_PASSWORD`: macOS signing and
    notarization (optional; without them the DMG is ad-hoc signed).
  - `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`,
    `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`: Android release signing
    (without them the APK is skipped). Keep a backup of the keystore: an app
    signed with a lost key can never be updated.
- **Repository settings**: ruleset `protect-main` blocks force pushes to and
  deletion of `main`; *Actions → General* allows only GitHub-owned actions,
  gives workflows read-only tokens by default, and does not let Actions
  create or approve pull requests.

Workflow rules (details in the workflow's header): manual dispatch only; no
tests, workflow artifacts or caches of the source, because this
repository's logs and artifacts are public; GitHub-owned actions pinned to
commits and hash-locked pip requirements only.
