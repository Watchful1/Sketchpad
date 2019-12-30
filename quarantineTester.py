import praw

r = praw.Reddit("Watchful1BotTest")
comment = r.comment("esm3ddt")
comment.reply("Bot test comment")

