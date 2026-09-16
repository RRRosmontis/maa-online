#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME="$ROOT/runtime"
mkdir -p "$RUNTIME/bin" "$RUNTIME/home" "$ROOT/config/profiles" "$ROOT/config/tasks"

python3 -m venv "$RUNTIME/venv"
"$RUNTIME/venv/bin/pip" install --upgrade pip
"$RUNTIME/venv/bin/pip" install -r "$ROOT/backend/requirements.txt"

MAA_INSTALL_DIR="$RUNTIME/bin" \
  bash -c 'curl -fsSL https://raw.githubusercontent.com/MaaAssistantArknights/maa-cli/main/install.sh | bash'

HOME="$RUNTIME/home" MAA_CONFIG_DIR="$ROOT/config" "$RUNTIME/bin/maa" install stable --batch
sed "s|__ROOT__|$ROOT|g" "$ROOT/config/profiles/cloud.toml.example" > "$ROOT/config/profiles/cloud.toml"
if [ ! -e "$ROOT/user_config/daily.toml" ]; then
    cp "$ROOT/user_config/daily.example.toml" "$ROOT/user_config/daily.toml"
fi
ln -sfn ../../user_config/daily.toml "$ROOT/config/tasks/daily.toml"
chmod 755 "$ROOT"/bin/* "$ROOT/backend/login.py" "$ROOT/user_config/edit_config.py"

cat <<EOF
Installation completed.
1. Request a login code: $RUNTIME/venv/bin/python $ROOT/backend/login.py request <phone>
2. Verify it:             $RUNTIME/venv/bin/python $ROOT/backend/login.py verify <code>
3. Start backend:         $ROOT/bin/maa-online-server
4. Start cloud session:   curl -X POST http://127.0.0.1:22888/start
5. Run daily:             $ROOT/bin/maa-online run daily --batch -v
EOF
