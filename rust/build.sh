#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/../cli"
BINS="volc-gen volc-websearch"
BUILD_MODE="${1:-local}"
HOST_OS="$(uname -s)"

cd "$SCRIPT_DIR"

mkdir -p "$CLI_DIR/macos" "$CLI_DIR/linux"

build_macos() {
  local target="aarch64-apple-darwin"
  echo "==> Building for macOS ($target)..."
  rustup target add "$target" 2>/dev/null || true
  cargo build --release --target "$target"
  for bin in $BINS; do
    cp "target/$target/release/$bin" "$CLI_DIR/macos/$bin"
  done
  echo "    macOS binaries:"
  ls -lh "$CLI_DIR"/macos/volc-*
}

build_linux() {
  local target="x86_64-unknown-linux-gnu"
  echo "==> Building for Linux ($target)..."
  rustup target add "$target" 2>/dev/null || true

  if cargo zigbuild --help &>/dev/null; then
    cargo zigbuild --release --target "$target"
    for bin in $BINS; do
      cp "target/$target/release/$bin" "$CLI_DIR/linux/$bin"
    done
    echo "    Linux binaries:"
    ls -lh "$CLI_DIR"/linux/volc-*
  elif command -v cross &>/dev/null; then
    cross build --release --target "$target"
    for bin in $BINS; do
      cp "target/$target/release/$bin" "$CLI_DIR/linux/$bin"
    done
    echo "    Linux binaries:"
    ls -lh "$CLI_DIR"/linux/volc-*
  else
    echo "    SKIP: Install cargo-zigbuild or cross for Linux builds."
    echo "      cargo install cargo-zigbuild && brew install zig"
    echo "      -- or --"
    echo "      cargo install cross"
  fi
}

case "$BUILD_MODE" in
  local)
    case "$HOST_OS" in
      Darwin)
        build_macos
        ;;
      Linux)
        build_linux
        ;;
      *)
        echo "Unsupported host OS: $HOST_OS"
        echo "Usage: bash build.sh [all]"
        exit 1
        ;;
    esac
    ;;
  all)
    build_macos
    build_linux
    ;;
  *)
    echo "Unknown build mode: $BUILD_MODE"
    echo "Usage: bash build.sh [all]"
    exit 1
    ;;
esac

echo ""
echo "Done. Run install-cli.sh to install to /usr/local/bin."
