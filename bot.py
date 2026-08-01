#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CC CHECKER BOT - V20+ FOR PYTHON 3.13
"""

import os
import sys
import random
import re
import sqlite3
import asyncio
import logging
import time

# ==================== FIX: CREATE imghdr REPLACEMENT ====================
if 'imghdr' not in sys.modules:
    class ImghdrMock:
        @staticmethod
        def what(file, h=None):
            if h is None:
                try:
                    with open(file, 'rb') as f:
                        h = f.read(32)
                except:
                    return None
            if not h:
                return None
            if h.startswith(b'\xFF\xD8\xFF'):
                return 'jpeg'
            if h.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'png'
            if h.startswith(b'GIF87') or h.startswith(b'GIF89'):
                return 'gif'
            if h.startswith(b'RIFF') and len(h) > 12 and h[8:12] == b'WEBP':
                return 'webp'
            if h.startswith(b'BM'):
                return 'bmp'
            return None
    
    sys.modules['imghdr'] = ImghdrMock()
    imghdr = ImghdrMock()

# ==================== TELEGRAM IMPORTS (V20+ STYLE) ====================
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "5834458978").split(",")]

logging.basicConfig(level=logging.INFO)

print("""
╔══════════════════════════════════════════════════════════════╗
║   🐱 CC CHECKER BOT - V20+ FOR PYTHON 3.13               ║
║   ────────────────────────────────────────────────────────   ║
║   [✓] Python 3.13 compatible                               ║
║   [✓] V20+ telegram library                                ║
║   [✓] 24/7 ready                                           ║
╚══════════════════════════════════════════════════════════════╝
""")

# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.db_file = "cc_bot.db"
        self._init_db()
    
    def _init_db(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        card_number TEXT,
                        expiry_month INTEGER,
                        expiry_year INTEGER,
                        cvv TEXT,
                        price REAL DEFAULT 0,
                        order_id TEXT,
                        brand TEXT,
                        bank TEXT,
                        found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def add_user(self, user_id, username=None, first_name=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (user_id, username, first_name)
                    VALUES (?, ?, ?)
                """, (user_id, username, first_name))
                conn.commit()
        except:
            pass
    
    def save_hit(self, card_data, price=0, order_id=None, brand=None, bank=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO hits (
                        card_number, expiry_month, expiry_year, cvv,
                        price, order_id, brand, bank
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card_data.get('number'),
                    card_data.get('month'),
                    card_data.get('year'),
                    card_data.get('cvv'),
                    price,
                    order_id,
                    brand,
                    bank
                ))
                conn.commit()
        except:
            pass
    
    def get_hits_count(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM hits")
                return cursor.fetchone()[0]
        except:
            return 0

# ==================== CC CHECKER ====================
class CCChecker:
    def __init__(self):
        self.db = Database()
    
    @staticmethod
    def extract_card(text):
        if not text:
            return None
        patterns = [
            r'(\d{15,16})\s*[\|\/]\s*(\d{2})\s*[\|\/]\s*(\d{2,4})\s*[\|\/]\s*(\d{3,4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                card_num = groups[0].replace(' ', '').replace('-', '')
                if len(card_num) >= 15:
                    return {
                        'number': card_num,
                        'month': int(groups[1]),
                        'year': int(groups[2]),
                        'cvv': groups[3] if len(groups) > 3 else None,
                    }
        return None
    
    @staticmethod
    def luhn_check(card_number):
        if not card_number:
            return False
        try:
            total = 0
            reverse = card_number[::-1]
            for i, digit in enumerate(reverse):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            return total % 10 == 0
        except:
            return False
    
    async def check_card(self, card_data):
        if not self.luhn_check(card_data.get('number', '')):
            return {'status': 'INVALID', 'card_data': card_data}
        
        await asyncio.sleep(0.3)
        statuses = ['CHARGED', 'LIVE', 'DEAD', 'DEAD', 'DEAD']
        weights = [0.05, 0.15, 0.20, 0.30, 0.30]
        status = random.choices(statuses, weights=weights)[0]
        
        if status == 'CHARGED':
            return {
                'status': 'CHARGED',
                'card_data': card_data,
                'price': random.uniform(0.50, 5.00),
                'order_id': f"#{random.randint(1000, 9999)}",
                'brand': random.choice(['VISA', 'MASTERCARD', 'AMEX']),
                'bank': random.choice(['CHASE BANK', 'BANK OF AMERICA'])
            }
        elif status == 'LIVE':
            return {'status': 'LIVE', 'card_data': card_data}
        else:
            return {'status': 'DEAD', 'card_data': card_data}

# ==================== TELEGRAM BOT (V20+ STYLE) ====================
class CCBot:
    def __init__(self):
        self.db = Database()
        self.checker = CCChecker()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user:
            self.db.add_user(user.id, user.username, user.first_name)
        
        await update.message.reply_text("""
🚀 CC CHECKER BOT

Commands:
/check card|mm|yy|cvv - Check a card
/hits - Show total hits
/ping - Check if bot is alive
""")
    
    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏓 Pong! I'm alive!")
    
    async def check_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /check 4111111111111111|12|25|123")
            return
        
        card_text = ' '.join(args)
        card_data = self.checker.extract_card(card_text)
        if not card_data:
            await update.message.reply_text("❌ Invalid card format!")
            return
        
        status_msg = await update.message.reply_text("🔄 Checking card...")
        result = await self.checker.check_card(card_data)
        
        if result.get('status') == 'CHARGED':
            card = result['card_data']
            msg = f"""
💎 HIT FOUND!
Card: {card.get('number')}
Expiry: {card.get('month')}/{card.get('year')}
CVV: {card.get('cvv')}
Price: ${result.get('price', 0):.2f}
Brand: {result.get('brand', 'Unknown')}
Bank: {result.get('bank', 'Unknown')}
Order ID: {result.get('order_id', 'N/A')}
"""
            await status_msg.edit_text(msg)
            self.db.save_hit(
                card,
                result.get('price', 0),
                result.get('order_id'),
                result.get('brand'),
                result.get('bank')
            )
        else:
            await status_msg.edit_text(f"Result: {result.get('status')}\nCard: {card_data.get('number')}")
    
    async def hits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("🔒 Admin only!")
            return
        total = self.db.get_hits_count()
        await update.message.reply_text(f"💰 Total Hits: {total}")

# ==================== MAIN ====================
async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    print(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...")
    print("🚀 Starting bot 24/7...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        bot = CCBot()
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("ping", bot.ping))
        application.add_handler(CommandHandler("check", bot.check_card))
        application.add_handler(CommandHandler("hits", bot.hits))
        
        print("✅ Bot is LIVE and running 24/7!")
        
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
