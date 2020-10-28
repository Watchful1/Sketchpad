import argparse

parser = argparse.ArgumentParser(description="Reddit RemindMe bot")
parser.add_argument("user", help="The reddit user account to use")
parser.add_argument("--once", help="Only run the loop once", action='store_const', const=True, default=False)
parser.add_argument("--debug_db", help="Use the debug database", action='store_const', const=True, default=False)
parser.add_argument(
	"--no_post", help="Print out reddit actions instead of posting to reddit", action='store_const', const=True,
	default=False)
parser.add_argument(
	"--no_backup", help="Don't backup the database", action='store_const', const=True, default=False)
parser.add_argument(
	"--reset_comment", help="Reset the last comment read timestamp", action='store_const', const=True,
	default=False)
parser.add_argument("--debug", help="Set the log level to debug", action='store_const', const=True, default=False)
parser.add_argument(
	"--pushshift", help="Select the pushshift client to use", action='store',
	choices=["prod", "beta", "auto"], default="prod")
args = parser.parse_args()

if args.pushshift == "prod":
	print("Passing in prod")
elif args.pushshift == "beta":
	print("Passing in beta")
elif args.pushshift == "auto":
	print("Passing in auto")
else:
	print("Invalid")

print("done")
