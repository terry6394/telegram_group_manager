import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Set, Any, Optional

from dotenv import load_dotenv
from telegram import Update, Message, Chat
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
    ContextTypes
)

# 加载环境变量
load_dotenv()

# 配置日志
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志格式
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_file = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")

# 配置日志处理器
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=log_format,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 从环境变量获取机器人令牌
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("未设置BOT_TOKEN环境变量。请在.env文件中设置。")

import json
import openai
import httpx

# LLM 配置（可由管理员通过 /llm_config 设置，默认值）
llm_config = {
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "api_key": ""
}
# openai 配置将由 load_deletion_config 读取并应用

# 配置文件路径
# 数据目录设置
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 配置文件路径
GROUPS_CONFIG_FILE = os.path.join(DATA_DIR, 'groups.json')
DELETION_QUEUE_FILE = os.path.join(DATA_DIR, 'deletion_queue.json')
DELETION_CONFIG_FILE = os.path.join(DATA_DIR, 'deletion_config.json')

# 存储需要监控的群组
monitored_groups: Dict[int, Dict[str, Any]] = {}
deletion_queue: List[Dict[str, Any]] = []
deletion_time: str = '00:00'
classification_prompt: str = ''
# 保存定时任务引用
_deletion_job = None

def load_monitored_groups():
    global monitored_groups
    try:
        with open(GROUPS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            groups = json.load(f)
            monitored_groups = {g['id']: {"name": g["name"]} for g in groups}
    except Exception as e:
        logging.warning(f"加载群组配置失败: {e}")
        monitored_groups = {}

def save_monitored_groups():
    groups = [{"id": gid, "name": info["name"]} for gid, info in monitored_groups.items()]
    try:
        with open(GROUPS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"保存群组配置失败: {e}")

def load_deletion_queue():
    global deletion_queue
    try:
        with open(DELETION_QUEUE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            deletion_queue = data
        elif isinstance(data, dict):
            deletion_queue = [data]
            logging.warning("deletion_queue.json contains an object, converted to list")
        else:
            deletion_queue = []
            logging.warning("deletion_queue.json unexpected format, reset to empty list")
    except Exception as e:
        logging.warning(f"加载删除队列失败: {e}")
        deletion_queue = []

def save_deletion_queue():
    try:
        with open(DELETION_QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(deletion_queue, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"保存删除队列失败: {e}")

def load_deletion_config():
    global deletion_time, classification_prompt, llm_config
    try:
        with open(DELETION_CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            deletion_time = cfg.get('deletion_time', deletion_time)
            classification_prompt = cfg.get('classification_prompt', classification_prompt)
            # 新增 LLM 配置加载
            if 'llm_config' in cfg:
                llm_config.update(cfg['llm_config'])
    except Exception as e:
        logging.warning(f"加载删除配置失败: {e}")
    # 应用 LLM 配置到 openai
    openai.api_key = llm_config.get("api_key", "")
    openai.api_base = llm_config.get("base_url", "https://api.openai.com/v1")

def save_deletion_config():
    try:
        with open(DELETION_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'deletion_time': deletion_time,
                'classification_prompt': classification_prompt,
                'llm_config': llm_config
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"保存删除配置失败: {e}")


# 启动时加载配置
def initialize_monitored_groups():
    load_monitored_groups()
    load_deletion_queue()
    load_deletion_config()

initialize_monitored_groups()

# 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    await update.message.reply_text(
        "Hello! I'm a Telegram group management bot that deletes inappropriate content based on message reactions.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command and show usage"""
    help_text = (
        "<b>🤖 Telegram Group Management Bot Help</b>\n\n"
        "<b>Basic Commands:</b>\n"
        "  /start - Start the bot\n"
        "  /help - Show this help message\n"
        "  /monitor - Enable reaction monitoring in current group\n"
        "  /stopmonitor - Disable reaction monitoring in current group\n"
        "  /status - Show current group status and pending deletions\n"
        "  /set_deletion_time HH:MM - Schedule daily deletion of 💩-marked messages at given time\n"
        "  /trigger_deletion - Manually trigger batch deletion now\n"
        "  /set_classification_prompt [prompt text] - Set LLM classification prompt (admin only)\n\n"
        "<b>Features:</b>\n"
        "  • LLM-based moderation: Each message is classified by LLM. If classified as DELETE, the bot will react with 🙈 (supported Telegram reaction emoji).\n"
        "  • 💩 reaction: Messages with 1 or more 💩 reactions are deleted immediately.\n"
        "  • 👎 reaction: Messages with 👎 reactions are queued for daily batch deletion.\n"
        "  • Only supported Telegram emoji can be used for reactions (e.g., 🙈, 💩, 👎, 👍, ❤️, 🔥, etc.).\n"
        "  • Bot must be admin with delete permissions.\n"
        "\n<b>Examples:</b>\n"
        "  /set_deletion_time 23:00\n"
        "  /status\n"
        "  /trigger_deletion\n"
        "\n<b>Environment:</b>\n"
        "  • Use conda_active.sh to update/activate the conda environment.\n"
        "  • Use Docker and start.sh for containerized deployment.\n"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /monitor command to start monitoring current group"""
    chat = update.effective_chat
    
    # 确认是群组
    if chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # 检查机器人是否为管理员
    from telegram import ChatMemberAdministrator, ChatMemberOwner
    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if isinstance(bot_member, (ChatMemberAdministrator, ChatMemberOwner)):
        if not bot_member.can_delete_messages:
            await update.message.reply_text("Please ensure I have permission to delete messages!")
            return
    else:
        await update.message.reply_text("Please make me an admin with delete permissions to operate properly.")
        return
    
    # 添加到监控列表
    monitored_groups[chat.id] = {
        "name": chat.title
    }
    save_monitored_groups()
    await update.message.reply_text("Reaction monitoring enabled for this group.")

async def stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stopmonitor command to stop monitoring current group"""
    chat = update.effective_chat
    
    if chat.id in monitored_groups:
        del monitored_groups[chat.id]
        save_monitored_groups()
        await update.message.reply_text("Stopped reaction monitoring for this group.")
    else:
        await update.message.reply_text("This group is not currently being monitored.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command and show group status"""
    import pytz
    from datetime import datetime as dt
    chat = update.effective_chat
    now = dt.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    deletion_count = len([item for item in deletion_queue if item['chat_id'] == chat.id])
    
    if chat.id in monitored_groups:
        info = monitored_groups[chat.id]
        msg = (
            f"<b>Group Monitoring Status</b>\n"
            f"Group Name: <code>{info.get('name', 'Unknown')}</code>\n"
            f"Group ID: <code>{chat.id}</code>\n"
            f"Current Time: <code>{now}</code>\n"
            f"💩 Pending Deletions: <b>{deletion_count}</b> messages\n"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text("This group is not currently monitored.")

async def set_deletion_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /set_deletion_time command to set daily batch deletion time"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /set_deletion_time HH:MM")
        return
    time_str = context.args[0]
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("Invalid time format. Please use HH:MM (24-hour format).")
        return
    
    global deletion_time, _deletion_job
    deletion_time = time_str
    save_deletion_config()
    
    # 移除旧任务
    if _deletion_job:
        try:
            _deletion_job.schedule_removal()
            logger.info(f"[定时任务] 已移除旧定时任务")
        except Exception as e:
            logger.warning(f"[定时任务] 移除旧定时任务失败: {e}")
    
    # 安排新任务
    await schedule_next_deletion(context)
    await update.message.reply_text(
        f"Daily deletion time set to {deletion_time}. Next run at {get_next_run_time(deletion_time).strftime('%Y-%m-%d %H:%M:%S')}"
    )

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理消息反应事件并根据规则删除消息"""
    reaction = update.message_reaction
    if not reaction:
        return
    
    chat_id = reaction.chat.id
    
    # 检查该群组是否被监控
    if chat_id not in monitored_groups:
        return
    
    # 获取新增的反应
    new_reactions = reaction.new_reaction
    
    # 💩 reaction: delete immediately
    for react in new_reactions:
        if hasattr(react, 'emoji') and react.emoji == "💩":
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=reaction.message_id
                )
                logger.info(f"Deleted message {reaction.message_id} from group {chat_id} due to 💩 reaction.")
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            return

    # 👎 reaction: add to batch deletion queue
    thumbs_down_count = 0
    for react in new_reactions:
        if hasattr(react, 'type') and react.type == 'emoji' and hasattr(react, 'emoji') and react.emoji == "👎":
            thumbs_down_count += 1
    threshold = 1
    if thumbs_down_count >= threshold:
        deletion_queue.append({'chat_id': chat_id, 'message_id': reaction.message_id})
        save_deletion_queue()
        logger.info(f"Queued message {reaction.message_id} from group {chat_id} due to {thumbs_down_count} 👎 reactions.")

async def handle_reaction_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理匿名消息反应计数更新事件"""
    reaction_count = update.message_reaction_count
    if not reaction_count:
        return
    
    chat_id = reaction_count.chat.id
    
    # 检查该群组是否被监控
    if chat_id not in monitored_groups:
        return
    
    # 检查是否有👎反应，以及数量是否超过阈值
    thumbs_down_count = 0
    for reaction in reaction_count.reactions:
        if hasattr(reaction.type, 'type') and reaction.type.type == 'emoji' and hasattr(reaction.type, 'emoji') and reaction.type.emoji == "👎":
            thumbs_down_count = reaction.total_count
            break
    
    # 设置阈值，当👎反应达到或超过此阈值时删除消息
    # 这里设置为3，匿名反应通常需要更高的阈值
    threshold = 3
    
    if thumbs_down_count >= threshold:
        try:
            # 删除原始消息
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=reaction_count.message_id
            )
            logger.info(
                f"Deleted message {reaction_count.message_id} from group {chat_id} due to {thumbs_down_count} anonymous 👎 reactions"
            )
            
            # 可选：发送通知
            await context.bot.send_message(
                chat_id=chat_id,
                text="A message has been deleted due to multiple negative reactions."
            )
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理错误"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # 获取发生错误的聊天ID（如果可用）
    if isinstance(update, Update) and update.effective_chat:
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text="An error occurred while processing your request. Please try again later."
        )

async def check_admin_status(context: ContextTypes.DEFAULT_TYPE) -> None:
    """定期检查机器人在监控的群组中是否仍然具有管理员权限"""
    bot = context.bot
    groups_to_remove = []
    
    for chat_id, info in monitored_groups.items():
        try:
            # 获取机器人在该群组中的成员信息
            bot_member = await bot.get_chat_member(chat_id, bot.id)
            
            # 检查是否有删除消息的权限
            if not bot_member.can_delete_messages:
                logger.warning(f"Bot lost delete message permission in group {info['name']} (ID: {chat_id})")
                groups_to_remove.append(chat_id)
                
                # 通知群组
                await bot.send_message(
                    chat_id=chat_id,
                    text="I no longer have permission to delete messages. Stopping monitoring for this group."
                )
        except Exception as e:
            logger.error(f"Failed to check admin status for group {chat_id}: {e}")
            groups_to_remove.append(chat_id)
    
    # 从监控列表中移除没有权限的群组
    for chat_id in groups_to_remove:
        if chat_id in monitored_groups:
            del monitored_groups[chat_id]
            logger.info(f"Removed group {chat_id} from monitoring list")

def get_next_run_time(time_str):
    """计算下一次运行的时间"""
    import pytz
    from datetime import datetime, timedelta
    
    # 当前时间（东八区）
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    
    # 解析目标时间
    hour, minute = map(int, time_str.split(':'))
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 如果目标时间已过，则设置为明天同一时间
    if target_time <= now:
        target_time += timedelta(days=1)
    
    logger.info(f"[定时任务] Next run time set to: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
    return target_time

async def schedule_next_deletion(context):
    """安排下一次删除任务"""
    global _deletion_job
    next_run_time = get_next_run_time(deletion_time)
    _deletion_job = context.job_queue.run_once(
        process_deletion_queue_wrapper,
        when=next_run_time
    )
    logger.info(f"[定时任务] Scheduled next deletion task for {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")

async def process_deletion_queue_wrapper(context):
    """删除任务的包装器，执行完成后自动调度下一次任务"""
    await process_deletion_queue(context)
    await schedule_next_deletion(context)

async def process_deletion_queue(context: ContextTypes.DEFAULT_TYPE) -> None:
    global deletion_queue
    # 过滤无效 entry
    valid_entries = [
        entry for entry in deletion_queue
        if isinstance(entry, dict) and 'chat_id' in entry and 'message_id' in entry
    ]
    if len(valid_entries) < len(deletion_queue):
        logger.warning(f"Found invalid entries in deletion_queue, will ignore them. Total: {len(deletion_queue)}, valid: {len(valid_entries)}")
    deletion_queue = valid_entries
    """批量删除待处理队列中的消息"""
    bot = context.bot
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("[定时任务] Running batch deletion task, current time: %s, queue length: %d", current_time, len(deletion_queue))
    failed: List[Dict[str, Any]] = []
    
    # 收集需要发送通知的群组
    chat_ids = set()
    for entry in deletion_queue:
        chat_ids.add(entry['chat_id'])
    
    if not deletion_queue:
        logger.info("[定时任务] No messages to delete, skipping.")
        return
    
    # 开始时发送通知
    for chat_id in chat_ids:
        if chat_id in monitored_groups:  # 只向被监控的群组发送通知
            try:
                count = len([item for item in deletion_queue if item['chat_id'] == chat_id])
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Starting batch deletion of {count} messages..."
                )
            except Exception as e:
                logger.error(f"[定时任务] Failed to send start notification: {e}")
    
    # 执行删除
    deleted_count = 0
    successful_deletions = []
    for entry in deletion_queue:
        try:
            await bot.delete_message(chat_id=entry['chat_id'], message_id=entry['message_id'])
            logger.info(f"[定时任务] Deleted message {entry['message_id']} from group {entry['chat_id']}")
            deleted_count += 1
            successful_deletions.append(entry)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"[定时任务] Failed to delete message: chat_id={entry['chat_id']} message_id={entry['message_id']} error: {e}")
            failed.append(entry)
    
    # 更新队列 - 清除所有消息，不保留失败的消息
    deletion_queue = []
    save_deletion_queue()
    logger.info("[定时任务] Batch deletion task completed, all messages cleared from queue")
    
    # 完成时发送通知
    for chat_id in chat_ids:
        if chat_id in monitored_groups:  # 只向被监控的群组发送通知
            try:
                failed_count = len([item for item in failed if item['chat_id'] == chat_id])
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Batch deletion completed! Deleted {deleted_count} messages, failed to delete {failed_count} messages."
                )
            except Exception as e:
                logger.error(f"[定时任务] Failed to send completion notification: {e}")

async def set_classification_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /set_classification_prompt command to set LLM classification system prompt"""
    chat = update.effective_chat
    if chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    from telegram import ChatMemberAdministrator, ChatMemberOwner
    user_member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if not isinstance(user_member, (ChatMemberAdministrator, ChatMemberOwner)):
        await update.message.reply_text("Only group admins can set classification prompt.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /set_classification_prompt <prompt text>")
        return
    global classification_prompt
    classification_prompt = ' '.join(context.args)
    save_deletion_config()
    await update.message.reply_text("Classification prompt updated.")

async def classify_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Classify each message via LLM and flag for deletion if needed"""
    message = update.message
    chat = message.chat
    if chat.id not in monitored_groups or not classification_prompt or not message.text:
        return
    try:
        # 动态设置 openai 配置
        openai.api_key = llm_config.get("api_key", "")
        openai.api_base = llm_config.get("base_url", "https://api.openai.com/v1")
        model = llm_config.get("model", "gpt-4o-mini")
        system_msg = f"{classification_prompt}\n\n请只回答 'DELETE' 或 'KEEP'。"
        logger.info(f"[LLM分类] prompt: {system_msg}")
        logger.info(f"[LLM分类] user message: {message.text}")
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": message.text}
            ],
            temperature=0
        )
        logger.info(f"[LLM分类] raw response: {response}")
        decision = response.choices[0].message.content.strip().upper()
        logger.info(f"[LLM分类] decision: {decision}")
        if decision.startswith("DELETE"):
            deletion_queue.append({'chat_id': chat.id, 'message_id': message.message_id})
            save_deletion_queue()
            # 1. 使用 Telegram setMessageReaction API 添加 reaction
            import os
            import httpx
            BOT_TOKEN = os.getenv("BOT_TOKEN")
            reaction_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
            payload = {
                "chat_id": chat.id,
                "message_id": message.message_id,
                "reaction": [{"type": "emoji", "emoji": "🙈"}]
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(reaction_url, json=payload)
                    logger.info(f"[LLM分类] setMessageReaction response: {resp.text}")
            except Exception as e:
                logger.warning(f"[LLM分类] setMessageReaction API 调用失败: {e}")
    except Exception as e:
        logger.error(f"[LLM分类] Failed to classify message: {e}")

async def llm_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """管理员设置 LLM 配置 (base_url, model, apikey)"""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    from telegram import ChatMemberAdministrator, ChatMemberOwner
    user_member = await context.bot.get_chat_member(chat.id, user.id)
    if not isinstance(user_member, (ChatMemberAdministrator, ChatMemberOwner)):
        await update.message.reply_text("Only group admins can set LLM config.")
        return
    if len(context.args) != 3:
        await update.message.reply_text(
            "Usage: /llm_config <base_url> <model> <apikey>\n"
            "Example: /llm_config https://api.groq.com/openai/v1 llama3-70b-8192 YOUR_API_KEY"
        )
        return
    global llm_config
    llm_config["base_url"] = context.args[0]
    llm_config["model"] = context.args[1]
    llm_config["api_key"] = context.args[2]
    save_deletion_config()
    await update.message.reply_text(
        f"LLM 配置已更新:\nBase URL: {llm_config['base_url']}\nModel: {llm_config['model']}\nAPI Key: {'*' * len(llm_config['api_key']) if llm_config['api_key'] else '(empty)'}"
    )

if __name__ == "__main__":
    # 创建应用程序
    application = Application.builder().token(TOKEN).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("monitor", monitor))
    application.add_handler(CommandHandler("stopmonitor", stop_monitor))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("set_deletion_time", set_deletion_time))
    application.add_handler(CommandHandler("llm_config", llm_config_command))
    
    # 手动触发删除命令
    async def trigger_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /trigger_deletion command to manually start batch deletion"""
        await update.message.reply_text("Manually triggering batch deletion...")
        await process_deletion_queue(context)
        await update.message.reply_text("Batch deletion complete")
    
    application.add_handler(CommandHandler("trigger_deletion", trigger_deletion))
    
    # 添加反应处理器
    application.add_handler(MessageReactionHandler(handle_reaction))
    
    # 添加匿名反应计数处理器
    application.add_handler(MessageReactionHandler(
        handle_reaction_count, 
        message_reaction_types=MessageReactionHandler.MESSAGE_REACTION_COUNT_UPDATED
    ))
    
    # 添加错误处理器
    application.add_error_handler(error_handler)
    
    # 添加定期检查管理员状态的任务（每小时检查一次）
    application.job_queue.run_repeating(check_admin_status, interval=3600)
    
    # 定时批量删除任务
    # 使用 run_once 而不是 run_daily，并在任务执行后自动调度下一次任务
    next_run_time = get_next_run_time(deletion_time)
    _deletion_job = application.job_queue.run_once(
        process_deletion_queue_wrapper,
        when=next_run_time
    )
    logger.info(f"[定时任务] Initialized scheduled deletion task for {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 新增 LLM 分类提示词设置命令
    application.add_handler(CommandHandler("set_classification_prompt", set_classification_prompt))
    
    # 新增 LLM 分类消息处理
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, classify_message))
    
    logger.info("Bot started...")
    
    # 使用内置的轮询方法启动机器人
    application.run_polling(
        allowed_updates=["message", "edited_channel_post", "callback_query", "message_reaction", "message_reaction_count"]
    )
