from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

TOKEN = "8781164789:AAFZT_YBZlDuVn1hjAOg9GtNHNSiCATxQVc"

# ======================
# KONEKSI GOOGLE SHEETS
# ======================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)

spreadsheet = client.open("FinanceBot")
sheet_accounts = spreadsheet.worksheet("Accounts")
sheet_trans = spreadsheet.worksheet("Transactions")


# ======================
# CEK SALDO
# ======================
def cek_saldo(update, context):
    accounts = sheet_accounts.get_all_records()

    if not accounts:
        update.message.reply_text("Belum ada akun.")
        return

    pesan = "Daftar Saldo:\n\n"

    for a in accounts:
        pesan += f"{a['Account']} : {a['Saldo']}\n"

    update.message.reply_text(pesan)


# ======================
# HANDLE TRANSAKSI
# ======================
def handle_message(update, context):
    try:
        text = update.message.text.lower()
        parts = text.split()

        if len(parts) < 4:
            update.message.reply_text(
                "Format:\n"
                "pengeluaran cash 25000 untuk makan\n"
                "pemasukan bca 100000 untuk gaji"
            )
            return

        jenis = parts[0]
        account = parts[1]
        nominal = int(parts[2])

        if "untuk" in parts:
            idx = parts.index("untuk")
            keterangan = " ".join(parts[idx+1:])
        else:
            keterangan = ""

        accounts = sheet_accounts.get_all_records()

        ditemukan = False

        for i, a in enumerate(accounts, start=2):
            if a["Account"].lower() == account:
                saldo_lama = int(a["Saldo"])
                ditemukan = True

                if jenis == "pengeluaran":
                    if saldo_lama < nominal:
                        update.message.reply_text("Saldo tidak cukup")
                        return
                    saldo_baru = saldo_lama - nominal
                    tipe = "pengeluaran"

                elif jenis == "pemasukan":
                    saldo_baru = saldo_lama + nominal
                    tipe = "pemasukan"

                else:
                    update.message.reply_text("Gunakan kata pengeluaran atau pemasukan")
                    return

                sheet_accounts.update_cell(i, 2, saldo_baru)

                sheet_trans.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    account.upper(),
                    tipe,
                    nominal,
                    keterangan,
                    saldo_baru
                ])

                update.message.reply_text(
                    f"Transaksi berhasil\n"
                    f"Akun: {account.upper()}\n"
                    f"Jenis: {tipe}\n"
                    f"Nominal: {nominal}\n"
                    f"Saldo sekarang: {saldo_baru}"
                )

                break

        if not ditemukan:
            update.message.reply_text("Account tidak ditemukan")

    except Exception as e:
        update.message.reply_text("Terjadi error")
        print(e)


# ======================
# START BOT
# ======================
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("saldo", cek_saldo))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

print("Bot berjalan...")
updater.start_polling()
updater.idle()