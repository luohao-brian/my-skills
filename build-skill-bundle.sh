#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/cli"
DIST_DIR="$SCRIPT_DIR/dist"
RUST_DIR="$SCRIPT_DIR/rust"

# ---- Build Rust binaries ----
echo "==> Building Rust binaries..."
cd "$RUST_DIR"
bash build.sh

# ---- Prepare dist ----
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# ---- Bundle function ----
# Usage: bundle_skill <skill-name> <binary-name>
bundle_skill() {
  local skill="$1"
  local bin="$2"
  local skill_src="$SCRIPT_DIR/$skill"

  for platform in macos linux; do
    local bin_src="$CLI_DIR/$platform/$bin"
    if [[ ! -f "$bin_src" ]]; then
      echo "    SKIP $platform: $bin_src not found"
      continue
    fi

    local staging="$DIST_DIR/_staging/$skill"
    rm -rf "$staging"
    mkdir -p "$staging/bin"

    # Copy skill files (SKILL.md, references/, etc.)
    # Use rsync to exclude hidden files and strip macOS extended attributes
    rsync -a --exclude='.*' "$skill_src/" "$staging/"

    # Copy binary and strip xattr
    cp "$bin_src" "$staging/bin/$bin"
    chmod +x "$staging/bin/$bin"

    # Strip macOS extended attributes to avoid Linux tar warnings
    if command -v xattr &>/dev/null; then
      xattr -cr "$staging"
    fi

    # Create tarball without macOS metadata (no-xattrs, no-mac-metadata)
    local tarball="$DIST_DIR/${skill}-${platform}.tar.gz"
    COPYFILE_DISABLE=1 tar -czf "$tarball" -C "$DIST_DIR/_staging" "$skill"
    echo "    Created: $tarball"
  done

  rm -rf "$DIST_DIR/_staging"
}

# ---- Bundle each skill ----
echo ""
echo "==> Bundling volc-gen..."
bundle_skill "volc-gen" "volc-gen"

echo "==> Bundling volc-websearch..."
bundle_skill "volc-websearch" "volc-websearch"

# ---- Summary ----
echo ""
echo "==> Done. Bundles:"
ls -lh "$DIST_DIR"/*.tar.gz

echo ""
echo "To install a skill, extract the tarball:"
echo "  tar xzf dist/volc-gen-macos.tar.gz -C ~/.openclaw/skills/"
echo "  tar xzf dist/volc-websearch-linux.tar.gz -C /path/to/workspace/skills/"
