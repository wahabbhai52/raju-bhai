import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Replace with your API ID, API Hash, and Bot Token
API_ID = "29490954"
API_HASH = "dbd8f5af56b0f6e16327c20a84eece99"
BOT_TOKEN = "8555817932:AAGigVzM-HE6PkoYJPWhYdPiU761jqSsERY"

# Telegram channel where files will be forwarded
CHANNEL_USERNAME = "@STUDENTZZZZBOT"  # Replace with your channel username

# Initialize Pyrogram Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store uploaded files temporarily
uploaded_files = {}
lock = asyncio.Lock()


# Function to extract names and URLs from the text file
def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data


# Function to categorize URLs
def categorize_urls(urls):
    videos, pdfs, others = [], [], []

    for name, url in urls:
        # Replace Utkarsh old domain with new domain
        if "apps-s3-jw-prod.utkarshapp.com/admin_v1" in url:
            url = url.replace(
                "https://apps-s3-jw-prod.utkarshapp.com/admin_v1",
                "https://d1q5ugnejk3zoi.cloudfront.net/ut-production-jw/admin_v1"
            )
            videos.append((name, url))

        # ✅ Handle online.utkarsh.com type links
        elif "online.utkarsh.com/utk/" in url:
            try:
                # Extract the part after utk/ and take only the number before "_"
                part = url.split("online.utkarsh.com/utk/")[1].split("_")[0]
                # Construct new CloudFront video URL
                new_url = f"https://d1q5ugnejk3zoi.cloudfront.net/ut-production-jw/admin_v1/file_library/videos/enc_plain_mp4/{part}/plain/720x1280.mp4"
                videos.append((name, new_url))
            except Exception:
                others.append((name, url))

        elif any(ext in url for ext in [".m3u8", ".mp4", "youtube.com", "classplusapp", "testbook", "videos.classplusapp.com"]):
            videos.append((name, url))

        elif url.lower().endswith(".pdf"):
            pdfs.append((name, url))
        else:
            others.append((name, url))

    return videos, pdfs, others


# Command handler for /start
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>𝗛𝗘𝗟𝗟𝗢 \n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "send me txt "
    )


# Handle file uploads
@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("❌ Please upload a .txt file only.")
        return

    async with lock:
        file_path = await message.download()
        file_name = message.document.file_name

        with open(file_path, "r") as f:
            file_content = f.read()

        urls = extract_names_and_urls(file_content)

        # Store uploaded file
        if message.from_user.id not in uploaded_files:
            uploaded_files[message.from_user.id] = []
        uploaded_files[message.from_user.id].append((file_name, urls, file_path, message))

        # Start processing after 10 seconds
        asyncio.create_task(process_files(client, message.from_user.id))


async def process_files(client, user_id):
    await asyncio.sleep(10)

    async with lock:
        if user_id not in uploaded_files:
            return

        files = uploaded_files.pop(user_id)
        if len(files) == 1:
            # Single file mode
            file_name, urls, file_path, msg = files[0]
            videos, pdfs, _ = categorize_urls(urls)

            # Video.txt
            if videos:
                video_file = file_path.replace(".txt", "_videos.txt")
                with open(video_file, "w") as vf:
                    for name, url in videos:
                        vf.write(f"{name}: {url}\n")
                await msg.reply_document(document=video_file, caption=f"⦿ 𝗕𝗔𝗧𝗖𝗛 ➤ {file_name} |\n 🎥 𝗧𝗼𝘁𝗮𝗹 𝗩𝗶𝗱𝗲𝗼𝘀 : {len(videos)}")
                os.remove(video_file)

            # PDF.txt
            if pdfs:
                pdf_file = file_path.replace(".txt", "_pdfs.txt")
                with open(pdf_file, "w") as pf:
                    for name, url in pdfs:
                        pf.write(f"{name}: {url}\n")
                await msg.reply_document(document=pdf_file, caption=f"⦿ 𝗕𝗔𝗧𝗖𝗛 ➤ {file_name} |\n 📂 𝗧𝗼𝘁𝗮𝗹 𝗣𝗗𝗙𝘀 : {len(pdfs)}")
                os.remove(pdf_file)

            await client.send_document(chat_id=CHANNEL_USERNAME, document=file_path)
            os.remove(file_path)

        else:
            # Multiple file mode (remove duplicates)
            all_urls = []
            for _, urls, _, _ in files:
                all_urls.extend(urls)

            seen = {}
            for name, url in all_urls:
                seen.setdefault(url, []).append(name)

            # Keep only unique URLs
            unique_urls = [(names[0], url) for url, names in seen.items() if len(names) == 1]

            first_file_name, _, first_file_path, msg = files[0]
            merged_file = first_file_path.replace(".txt", "_.txt")

            with open(merged_file, "w") as mf:
                for name, url in unique_urls:
                    mf.write(f"{name}: {url}\n")

            await msg.reply_document(document=merged_file, caption=f"⦿ 𝗕𝗔𝗧𝗖𝗛 ➤ {first_file_name} |\n 🟢 𝗧𝗢𝗧𝗔𝗟 ( 𝚅𝚒𝚍𝚎𝚘 + 𝙿𝚍𝚏 ) 𝙻𝙸𝙽𝙺𝚂 [𝗨𝗽𝗱𝗮𝘁𝗲] : {len(unique_urls)}")
            await client.send_document(chat_id=CHANNEL_USERNAME, document=merged_file)

            for _, _, file_path, _ in files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            os.remove(merged_file)


# Run bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
