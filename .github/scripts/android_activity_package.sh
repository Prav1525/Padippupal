#!/usr/bin/env bash
# Resolve package names from flattened --brief or braced ResolveInfo output.
resolve_activity_package() {
  local component="$1"
  component="$(printf '%s\n' "$component" | sed -E 's/.*\{([^}]*)\}.*/\1/; s/.*[[:space:]]//')"
  local package="${component%%/*}"
  if [[ ! "$package" =~ ^[A-Za-z0-9_]+([.][A-Za-z0-9_]+)+$ ]]; then
    return 1
  fi
  printf '%s\n' "$package"
}
