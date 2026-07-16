import argparse
import json
import sys


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep argparse failures machine-readable when --json was requested."""

    json_requested = False

    def error(self, message):
        if self.json_requested:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "status": "invalid_arguments",
                        "message": message,
                    },
                    ensure_ascii=False,
                )
            )
            self.print_usage(sys.stderr)
            self.exit(2)
        super().error(message)


def configure_json_argument_parser(argv):
    JsonArgumentParser.json_requested = "--json" in argv
    return JsonArgumentParser
