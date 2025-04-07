
# 1) Installer les dépendances (si dans Google Colab)
!pip install python-telegram-bot pymongo dnspython nest_asyncio openai --quiet

# 2) Imports
import os, nest_asyncio, openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)
from pymongo import MongoClient

TOKEN="8071092386:AAFEIopsYTKCzifcQ5pIGfPcyDNP5aC2WVY"

# 3) Exécution asynchrone (Colab)
nest_asyncio.apply() 

# 4) Clés d'API
TOKEN = os.getenv("BOT_TOKEN", "8071092386:AAFEIopsYTKCzifcQ5pIGfPcyDNP5aC2WVY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://jhonskyload:9RQEDyKAKPeqYaF1@cluster0.tabu1ts.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "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")

# 5) Connexion MongoDB
client = MongoClient(MONGO_URI)
db = client.smartimmobot
users = db.users
conversations = db.conversations


# 6) Menu principal
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛐 Aide", callback_data='aide')],
        [InlineKeyboardButton("🚨 Annonces", callback_data='annonces')],
        [InlineKeyboardButton("✍️ Demande", callback_data='demande')],
        [InlineKeyboardButton("🗕️ Rdv", callback_data='rdv')],
        [InlineKeyboardButton("💡 Conseils", callback_data='conseils')],
        [InlineKeyboardButton("❤️ Dons", callback_data='dons')],
        [InlineKeyboardButton("🤖 Parler à l'IA", callback_data='ia')]
    ])

def back_button(to='start'):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour", callback_data=to)]])

# 7) Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.update_one(
        {"id": user.id},
        {"$set": {"name": user.first_name, "username": user.username}},
        upsert=True
    )
    text = f"Bienvenue *{user.first_name}* sur *SmartImmoBot* !\nChoisissez une option :"
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_menu())


# 8) Gestion du menu principal
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    choice = query.data
    await query.answer()

    if choice == 'aide':
        text = (
            "*Aide - SmartImmoBot*\n\n"
            "/annonces - Voir les annonces\n"
            "/demande - Faire une demande\n"
            "/rdv - Prendre un rendez-vous\n"
            "/conseils - Recevoir des conseils\n"
            "/dons - Soutenir le projet\n"
            "Parlez à l'IA pour poser vos questions."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=back_button())

    elif choice in ('annonces','demande'):
        await query.edit_message_text(
            "Choisissez :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Location", callback_data=f"{choice}_location")],
                [InlineKeyboardButton("Vente", callback_data=f"{choice}_vente")],
                [InlineKeyboardButton("Filtrer", callback_data=f"{choice}_filtrer")],
                [InlineKeyboardButton("Retour", callback_data='start')],
            ])
        )

    elif choice == 'rdv':
        await query.edit_message_text("Fixez votre rendez-vous :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Date", callback_data='rdv_date')],
                [InlineKeyboardButton("Heure", callback_data='rdv_heure')],
                [InlineKeyboardButton("Retour", callback_data='start')],
            ])
        )

    elif choice == 'conseils':
        await query.edit_message_text("Choisissez un thème :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Achat", callback_data='conseil_achat')],
                [InlineKeyboardButton("Location", callback_data='conseil_location')],
                [InlineKeyboardButton("Vente", callback_data='conseil_vente')],
                [InlineKeyboardButton("Investissement", callback_data='conseil_invest')],
                [InlineKeyboardButton("Retour", callback_data='start')],
            ])
        )

    elif choice == 'dons':
        await query.edit_message_text("Soutenez-nous via :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Orange Money", callback_data='don_orange')],
                [InlineKeyboardButton("MTN Money", callback_data='don_mtn')],
                [InlineKeyboardButton("Retour", callback_data='start')],
            ])
        )

    elif choice == 'ia':
        await query.edit_message_text("🤖 Posez-moi une question ! Envoyez votre message.", reply_markup=back_button('start'))
        context.user_data['awaiting_ai'] = True

    elif choice == 'start':
        await start(update, context)

# 9) Sous-commandes
async def handle_subcommands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cmd = query.data
    await query.answer()

    messages = {
        'annonces_location': "https://site/location",
        'annonces_vente': "https://site/vente",
        'demande_location': "Envoyez vos besoins pour une location",
        'demande_vente': "Envoyez vos besoins pour une vente",
        'rdv_date': "Merci d'entrer la date souhaitée (JJ/MM/AAAA)",
        'rdv_heure': "Merci d'entrer l'heure souhaitée (HH:MM)",
        'conseil_achat': "Comparez les offres et inspectez bien !",
        'conseil_location': "Vérifiez les contrats, localisation et état du logement.",
        'conseil_vente': "Mettez en valeur le bien, fixez un bon prix.",
        'conseil_invest': "Choisissez un quartier porteur et diversifiez !",
        'don_orange': "Orange Money : 07 XX XX XX",
        'don_mtn': "MTN Money : 05 XX XX XX",
    }
    text = messages.get(cmd, "Désolé, commande inconnue.")

    if cmd.startswith("rdv_"):
        users.update_one({"id": query.from_user.id}, {"$push": {"rendezvous": {"etape": cmd, "valeur": text}}})

    await query.edit_message_text(text=text, reply_markup=back_button('start'))

# 10) Intelligence Artificielle (OpenRouter)
async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.effective_user.id

    if not context.user_data.get('awaiting_ai'):
        return

    messages = [{"role": "user", "content": user_input}]

    try:
        openai.api_key = OPENROUTER_KEY
        openai.api_base = "https://openrouter.ai/api/v1"

        response = openai.ChatCompletion.create(
            model="openrouter/auto",
            messages=messages
        )
        reply = response['choices'][0]['message']['content']
        await update.message.reply_text(reply)

        conversations.insert_one({"user_id": user_id, "question": user_input, "response": reply})
    except Exception as e:
        await update.message.reply_text("Erreur : Impossible de contacter l'IA. Veuillez réessayer.")

    context.user_data['awaiting_ai'] = False

# 11) Commande /mon_profil
async def mon_profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = users.find_one({"id": user.id})
    if not doc:
        await update.message.reply_text("Aucun profil trouvé. Envoyez /start.")
        return

    txt = f"*{doc['name']}* (@{doc.get('username','-')})\nID: `{doc['id']}`"
    if 'rendezvous' in doc:
        rdvs = "\n".join(f"- {r['valeur']}" for r in doc['rendezvous'])
        txt += f"\n\n*Vos RDV*:\n{rdvs}"
    await update.message.reply_text(txt, parse_mode='Markdown')

# 12) Statistiques
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = users.count_documents({})
    total_rdv = users.count_documents({"rendezvous": {"$exists": True}})
    await update.message.reply_text(
        f"*Statistiques* :\nUtilisateurs : {total_users}\nRDV : {total_rdv}", parse_mode='Markdown')

# 13) Application
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mon_profil", mon_profil))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CallbackQueryHandler(handle_main_menu, pattern='^(aide|annonces|demande|rdv|conseils|dons|ia|start)$')) # Fixed: pattern string is now on a single line
app.add_handler(CallbackQueryHandler(handle_subcommands))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message))

# 14) Lancer le bot
# Instead of directly calling run_polling(), use this:
import asyncio
async def run_bot():
  """Starts the bot and keeps it running."""
  await app.initialize() # Initialize the bot before starting
  # Use app.run_polling() instead of app.start_polling()
  await app.run_polling() # Start polling for updates
  # await app.idle() # Keep the bot running until it's stopped - This line might cause issues, so I have commented it out. If you want to use run_polling() you don't need to call app.idle()

# Only execute this if the script is run directly (not imported)
if __name__ == '__main__':
  try:
    asyncio.run(run_bot()) # Run the bot in an event loop
  except KeyboardInterrupt: # Allow graceful shutdown with Ctrl+C
    print("Bot stopped by user.")
  finally:
    asyncio.run(app.shutdown()) # Ensure the bot is shut down properly

#Ajouter un webhook ( port render)
import threading
from flask import Flask

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "SmartImmoBot fonctionne !"

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# Lancer Flask en parallèle
threading.Thread(target=run_flask).start()

# Démarrer le bot
app.run_polling()
