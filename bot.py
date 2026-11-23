
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = Path(os.getenv("DB_PATH", "profit.db"))

COST, PRICE, QUANTITY = range(3)


# ---------- DATABASE ----------

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cost TEXT NOT NULL,
                price TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                profit TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_calculation(user_id, cost, price, quantity, profit):
    with get_db() as db:
        db.execute("""
            INSERT INTO calculations
                (user_id, cost, price, quantity, profit, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            str(cost),
            str(price),
            quantity,
            str(profit),
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        ))


def format_money(value):
    return f"{value:,.2f}"


def parse_money(text):
    try:
        value = Decimal(text.strip().replace(",", "."))

        if not value.is_finite() or value < 0:
            return None

        if value.as_tuple().exponent < -2:
            return None

        return value
    except (InvalidOperation, ValueError):
        return None


# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Profit Calculator!\n\n"
        "Commands:\n"
        "/new - New calculation\n"
        "/history - Last 10 calculations\n"
        "/total - Total profit\n"
        "/cancel - Cancel calculation\n"
        "/help - Show commands"
    )


async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "💰 Enter purchase price per unit:"
    )
    return COST


async def get_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = parse_money(update.message.text)

    if value is None:
        await update.message.reply_text(
            "Please enter a valid non-negative price "
            "(maximum 2 decimal places)."
        )
        return COST

    context.user_data["cost"] = value

    await update.message.reply_text(
        "💵 Enter selling price per unit:"
    )
    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = parse_money(update.message.text)

    if value is None:
        await update.message.reply_text(
            "Please enter a valid non-negative price "
            "(maximum 2 decimal places)."
        )
        return PRICE

    context.user_data["price"] = value

    await update.message.reply_text(
        "📦 Enter quantity:"
    )
    return QUANTITY


async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantity = int(update.message.text.strip())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Please enter a positive whole number."
        )
        return QUANTITY

    cost = context.user_data["cost"]
    price = context.user_data["price"]

    revenue = price * quantity
    total_cost = cost * quantity
    profit = revenue - total_cost

    save_calculation(
        update.effective_user.id,
        cost, price, quantity, profit
    )

    await update.message.reply_text(
        "✅ Calculation saved!\n\n"
        f"📦 Quantity: {quantity}\n"
        f"💰 Revenue: {format_money(revenue)}\n"
        f"💸 Total cost: {format_money(total_cost)}\n"
        f"📈 Profit: {format_money(profit)}\n\n"
        "Use /new for another calculation."
    )

    context.user_data.clear()
    return ConversationHandler.END


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    with get_db() as db:
        rows = db.execute("""
            SELECT * FROM calculations
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (user_id,)).fetchall()

    if not rows:
        await update.message.reply_text(
            "📭 No calculations yet. Use /new!"
        )
        return

    lines = ["📜 Your last 10 calculations:\n"]

    for row in rows:
        profit = Decimal(row["profit"])

        lines.append(
            f"#{row['id']} | {row['created_at']}\n"
            f"Cost: {row['cost']} | Price: {row['price']}\n"
            f"Quantity: {row['quantity']}\n"
            f"Profit: {format_money(profit)}\n"
        )

    await update.message.reply_text("\n".join(lines))


async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    with get_db() as db:
        rows = db.execute("""
            SELECT profit FROM calculations
            WHERE user_id = ?
        """, (user_id,)).fetchall()

    total_profit = sum(
        (Decimal(row["profit"]) for row in rows),
        Decimal("0")
    )

    await update.message.reply_text(
        "📊 Your statistics\n\n"
        f"Calculations: {len(rows)}\n"
        f"Total profit: {format_money(total_profit)}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Calculation cancelled.")
    return ConversationHandler.END


# ---------- MAIN ----------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing!")

    init_db()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .build()
        )

    conversation = ConversationHandler(
        entry_points=[CommandHandler("new", new)],
        states={
            COST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_cost)
            ],
            PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)
            ],
            QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conversation)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("total", total))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
