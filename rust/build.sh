#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/../cli"
BINS="volc-gen volc-websearch"

cd "$SCRIPT_DIR"

mkdir -p "$CLI_DIR/macos" "$CLI_DIR/linux"

# ---- macOS (aarch64-apple-darwin) ----
MACOS_TARGET="aarch64-apple-darwin"
echo "==> Building for macOS ($MACOS_TARGET)..."
rustup target add "$MACOS_TARGET" 2>/dev/null || true
cargo build --release --target "$MACOS_TARGET"
for bin in $BINS; do
  cp "target/$MACOS_TARGET/release/$bin" "$CLI_DIR/macos/$bin"
done
echo "    macOS binaries:"
ls -lh "$CLI_DIR"/macos/volc-*

# ---- Linux (x86_64-unknown-linux-gnu) ----
LINUX_TARGET="x86_64-unknown-linux-gnu"
echo "==> Building for Linux ($LINUX_TARGET)..."
rustup target add "$LINUX_TARGET" 2>/dev/null || true

if cargo zigbuild --help &>/dev/null; then
  cargo zigbuild --release --target "$LINUX_TARGET"
  for bin in $BINS; do
    cp "target/$LINUX_TARGET/release/$bin" "$CLI_DIR/linux/$bin"
  done
  echo "    Linux binaries:"
  ls -lh "$CLI_DIR"/linux/volc-*
elif command -v cross &>/dev/null; then
  cross build --release --target "$LINUX_TARGET"
  for bin in $BINS; do
    cp "target/$LINUX_TARGET/release/$bin" "$CLI_DIR/linux/$bin"
  done
  echo "    Linux binaries:"
  ls -lh "$CLI_DIR"/linux/volc-*
else
  echo "    SKIP: Install cargo-zigbuild or cross for Linux builds."
  echo "      cargo install cargo-zigbuild && brew install zig"
  echo "      -- or --"
  echo "      cargo install cross"
fi

echo ""
echo "Done. Run install-cli.sh to install to /usr/local/bin."
