"""Start an agent from a private JSON configuration, before importing collectors."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    allowed = {"server_url", "system_id", "api_key", "data_dir", "ca_cert", "sysmon"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError("Unsupported agent configuration")
    for key in ("server_url", "system_id", "api_key", "data_dir"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError("Missing required agent configuration: " + key)
    origin = urlsplit(config["server_url"])
    if (origin.scheme != "https" or not origin.hostname or origin.username or origin.password
            or origin.path not in ("", "/") or origin.query or origin.fragment):
        raise ValueError("server_url must be an HTTPS origin")
    if len(config["api_key"]) < 32 or any(c in config["api_key"] for c in "\r\n"):
        raise ValueError("Invalid enrollment credential")
    if not Path(config["data_dir"]).is_absolute():
        raise ValueError("data_dir must be absolute")
    ca = config.get("ca_cert", "")
    if not isinstance(ca, str) or (ca and (not Path(ca).is_absolute() or not Path(ca).is_file())):
        raise ValueError("ca_cert must be an existing absolute certificate path")
    if not isinstance(config.get("sysmon", False), bool):
        raise ValueError("sysmon must be a boolean")
    return {"EDR_ENV": "production", "EDR_SERVER_URL": config["server_url"].rstrip("/"),
            "EDR_SYSTEM_ID": config["system_id"], "EDR_API_KEY": config["api_key"],
            "EDR_AGENT_DATA": config["data_dir"], "EDR_TLS_CA_CERT": ca,
            "EDR_SYSMON": str(config.get("sysmon", False)).lower(),
            "EDR_PROCESS_SOURCE": "sysmon" if config.get("sysmon", False) else "polling"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="Validate without starting collection")
    args = parser.parse_args()
    os.environ.update(load_config(args.config))
    if args.check:
        print("Agent configuration valid; credentials not displayed. Connectivity is not tested.")
    else:
        from agent import main
        main()
