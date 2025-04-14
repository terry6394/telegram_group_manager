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

# 存储需要监控的群组
monitored_groups: Dict[int, Dict[str, Any]] = {}

# 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/start命令"""
    await update.message.reply_text(
        "你好！我是一个群组管理机器人，可以根据消息反应删除不适当的内容。\n"
        "使用 /help 查看可用命令。"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/help命令"""
    help_text = (
        "可用命令:\n"
        "/start - 启动机器人\n"
        "/help - 显示此帮助信息\n"
        "/monitor - 开始监控当前群组的反应\n"
        "/stopmonitor - 停止监控当前群组\n"
        "/status - 显示机器人状态\n\n"
        "功能说明:\n"
        "- 当消息收到1个或更多👎反应时，该消息将被自动删除\n"
        "- 对于匿名反应，当消息收到3个或更多👎反应时，该消息将被自动删除\n"
        "- 机器人需要具有管理员权限并能够删除消息才能正常工作"
    )
    await update.message.reply_text(help_text)

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/monitor命令，开始监控当前群组"""
    chat = update.effective_chat
    
    # 确认是群组
    if chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    # 检查机器人是否为管理员
    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if not bot_member.can_delete_messages:
        await update.message.reply_text("请确保我有删除消息的权限！")
        return
    
    # 添加到监控列表
    monitored_groups[chat.id] = {
        "name": chat.title,
        "started_at": datetime.now(),
        "started_by": update.effective_user.id
    }
    
    await update.message.reply_text(f"已开始监控此群组的消息反应。")

async def stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/stopmonitor命令，停止监控当前群组"""
    chat = update.effective_chat
    
    if chat.id in monitored_groups:
        del monitored_groups[chat.id]
        await update.message.reply_text("已停止监控此群组。")
    else:
        await update.message.reply_text("此群组当前未被监控。")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/status命令，显示机器人状态"""
    chat = update.effective_chat
    
    if chat.id in monitored_groups:
        info = monitored_groups[chat.id]
        started_at = info["started_at"].strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(
            f"此群组正在被监控。\n"
            f"开始时间: {started_at}"
        )
    else:
        await update.message.reply_text("此群组当前未被监控。")

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
    
    # 检查是否有👎反应
    thumbs_down_count = 0
    for react in new_reactions:
        # 检查是否为emoji类型的反应，并且是👎
        if hasattr(react, 'type') and react.type == 'emoji' and hasattr(react, 'emoji') and react.emoji == "👎":
            thumbs_down_count += 1
    
    # 设置阈值，当👎反应达到或超过此阈值时删除消息
    # 这里设置为1，你可以根据需要调整
    threshold = 1

    if thumbs_down_count >= threshold:
        try:
            # 删除原始消息
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=reaction.message_id
            )
            logger.info(
                f"已删除消息 {reaction.message_id} 来自群组 {chat_id} 因为收到 {thumbs_down_count} 个👎反应"
            )
            
            # 可选：发送通知
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"一条消息因收到负面反应而被删除。"
            )
        except Exception as e:
            logger.error(f"删除消息失败: {e}")

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
                f"已删除消息 {reaction_count.message_id} 来自群组 {chat_id} 因为收到 {thumbs_down_count} 个匿名👎反应"
            )
            
            # 可选：发送通知
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"一条消息因收到多个负面反应而被删除。"
            )
        except Exception as e:
            logger.error(f"删除消息失败: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理错误"""
    logger.error(f"更新 {update} 导致错误 {context.error}")
    
    # 获取发生错误的聊天ID（如果可用）
    if isinstance(update, Update) and update.effective_chat:
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text="处理请求时出现错误，请稍后再试。"
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
                logger.warning(f"机器人在群组 {info['name']} (ID: {chat_id}) 中失去了删除消息的权限")
                groups_to_remove.append(chat_id)
                
                # 通知群组
                await bot.send_message(
                    chat_id=chat_id,
                    text="我不再具有删除消息的权限，已停止监控此群组。"
                )
        except Exception as e:
            logger.error(f"检查群组 {chat_id} 的管理员状态时出错: {e}")
            groups_to_remove.append(chat_id)
    
    # 从监控列表中移除没有权限的群组
    for chat_id in groups_to_remove:
        if chat_id in monitored_groups:
            del monitored_groups[chat_id]
            logger.info(f"已从监控列表中移除群组 {chat_id}")

if __name__ == "__main__":
    # 创建应用程序
    application = Application.builder().token(TOKEN).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("monitor", monitor))
    application.add_handler(CommandHandler("stopmonitor", stop_monitor))
    application.add_handler(CommandHandler("status", status))
    
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
    
    logger.info("机器人已启动...")
    
    # 使用内置的轮询方法启动机器人
    application.run_polling(
        allowed_updates=["message", "edited_channel_post", "callback_query", "message_reaction", "message_reaction_count"]
    )
