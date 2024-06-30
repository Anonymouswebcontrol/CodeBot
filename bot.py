import discord
from discord.ext import commands
import re
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Votre code du bot ici
print("Début du script")  # Débogage

# Liste des insultes à filtrer
bad_words = ['insulte1', 'insulte2', 'insulte3']

# Fonction pour détecter les insultes
def contains_bad_words(message):
    print("Vérification des insultes")  # Débogage
    return any(bad_word in message.content.lower() for bad_word in bad_words)

# Fonction pour détecter les liens Discord
def contains_discord_links(message):
    print("Vérification des liens Discord")  # Débogage
    discord_link_pattern = r"(https?:\/\/)?(www\.)?(discord\.(gg|com|me|io)\/.+)"
    return re.search(discord_link_pattern, message.content)

# Dictionnaire pour suivre les avertissements, bannissements et kicks
member_history = {}

def add_warning(member):
    if member.id not in member_history:
        member_history[member.id] = {"warnings": 0, "bans": 0, "kicks": 0}
    member_history[member.id]["warnings"] += 1

def add_ban(member):
    if member.id not in member_history:
        member_history[member.id] = {"warnings": 0, "bans": 0, "kicks": 0}
    member_history[member.id]["bans"] += 1

def add_kick(member):
    if member.id not in member_history:
        member_history[member.id] = {"warnings": 0, "bans": 0, "kicks": 0}
    member_history[member.id]["kicks"] += 1

# Définir les intents
intents = discord.Intents.default()
intents.messages = True  # Activer l'intent pour les messages
intents.guilds = True
intents.members = True
intents.presences = True

print("Intents définis")  # Débogage

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

print("Événements définis")  # Débogage

@bot.event
async def on_message(message):
    print(f"Message reçu : {message.content}")  # Débogage
    # Ne pas répondre à ses propres messages
    if message.author == bot.user:
        print("Message du bot ignoré")  # Débogage
        return

    # Filtrer et supprimer les insultes
    if contains_bad_words(message):
        print("Insulte détectée, suppression du message")  # Débogage
        await message.delete()
    
    # Filtrer et supprimer les liens Discord
    elif contains_discord_links(message):
        print("Lien Discord détecté, suppression du message")  # Débogage
        await message.delete()

    await bot.process_commands(message)

print("on_message défini")  # Débogage

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    print(f"Commande ban exécutée pour {member}")  # Débogage
    add_ban(member)
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} a été banni.')

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        print("Erreur de permissions pour la commande ban")  # Débogage
        await ctx.send('Vous n\'avez pas la permission de bannir des membres.')

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    print(f"Commande unban exécutée pour {member}")  # Débogage
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'{user.mention} a été débanni.')
            return
    
    await ctx.send(f"L'utilisateur {member} n'est pas dans la liste des bannis.")

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission d'exécuter cette commande.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Il manque un argument requis : {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Impossible de trouver cet utilisateur.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    print(f"Commande kick exécutée pour {member}")  # Débogage
    add_kick(member)
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} a été kické pour la raison suivante: {reason}')

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick_temp(ctx, member: discord.Member, duration: int, *, reason=None):
    print(f"Commande kick temporaire exécutée pour {member} pendant {duration} secondes")  # Débogage
    add_kick(member)
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} a été kické pour la raison suivante: {reason}. Il pourra rejoindre dans {duration} secondes.')

    await asyncio.sleep(duration)
    await ctx.guild.unban(member)
    await ctx.send(f'{member.mention} peut maintenant rejoindre à nouveau le serveur.')

@bot.command(name="mute_on")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    print(f"Commande mute exécutée pour {member}")  # Débogage
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.add_roles(mute_role, reason=reason)
    await ctx.send(f'{member.mention} a été muté pour la raison suivante: {reason}')

@bot.command(name="mute_off")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    print(f"Commande unmute exécutée pour {member}")  # Débogage
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.remove_roles(mute_role)
    await ctx.send(f'{member.mention} a été unmute.')

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute_list(ctx):
    print("Commande mute_list exécutée")  # Débogage
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if mute_role is None:
        await ctx.send("Le rôle Muted n'existe pas sur ce serveur.")
        return

    muted_members = [member for member in ctx.guild.members if mute_role in member.roles]
    if not muted_members:
        await ctx.send("Aucun membre n'est actuellement mute.")
    else:
        muted_list = "\n".join([member.display_name for member in muted_members])
        await ctx.send(f"Membres mute :\n{muted_list}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def ban_list(ctx):
    print("Commande ban_list exécutée")  # Débogage
    banned_members = await ctx.guild.bans()
    if not banned_members:
        await ctx.send("Aucun membre n'est actuellement banni.")
    else:
        banned_list = "\n".join([f"{entry.user.name}#{entry.user.discriminator} ({entry.user.id})" for entry in banned_members])
        await ctx.send(f"Membres bannis :\n{banned_list}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    print(f"Commande warn exécutée pour {member}")  # Débogage
    add_warning(member)

    # Envoi du message dans le salon
    await ctx.send(f'{member.mention}, vous avez été averti pour la raison suivante: {reason}')

    # Envoi du message en MP
    try:
        await member.send(f"Vous avez été averti sur le serveur '{ctx.guild.name}' pour la raison suivante: {reason}")
    except discord.Forbidden:
        await ctx.send(f"Impossible d'envoyer un message privé à {member.mention}. Veuillez vérifier vos paramètres de confidentialité.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """
    Efface un certain nombre de messages dans le canal.
    Usage : !clear <nombre de messages>
    """
    if amount <= 0:
        await ctx.send("Le nombre de messages à supprimer doit être supérieur à zéro.")
        return

    await ctx.message.delete()  # Supprime la commande !clear

    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"{len(deleted)} messages ont été supprimés.", delete_after=5)

@bot.command()
async def ping(ctx):
    print("Commande ping exécutée")  # Débogage
    await ctx.send('Pong!')

@bot.command()
@commands.has_permissions(manage_roles=True)
async def infos(ctx, member: discord.Member):
    print(f"Commande infos exécutée pour {member}")  # Débogage

    created_at = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
    joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")

    warnings = member_history.get(member.id, {}).get("warnings", 0)
    bans = member_history.get(member.id, {}).get("bans", 0)
    kicks = member_history.get(member.id, {}).get("kicks", 0)

    roles = [role for role in member.roles if role.name != "@everyone"]
    if roles:
        roles_str = " ".join([role.mention for role in roles])
    else:
        roles_str = "Aucun rôle"

    embed = discord.Embed(title=f"Informations sur {member.display_name}", color=discord.Color.blue())
    embed.add_field(name="Date de création du compte", value=created_at, inline=False)
    embed.add_field(name="Date d'arrivée sur le serveur", value=joined_at, inline=False)
    embed.add_field(name="Nombre d'avertissements", value=warnings, inline=False)
    embed.add_field(name="Nombre de bannissements", value=bans, inline=False)
    embed.add_field(name="Nombre de kicks", value=kicks, inline=False)
    embed.add_field(name="Rôles", value=roles_str, inline=False)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, new_nick):
    try:
        await member.edit(nick=new_nick)
        await ctx.send(f"Le pseudo de {member.mention} a été modifié avec succès.")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de modifier le pseudo de ce membre.")
    except discord.HTTPException:
        await ctx.send("Échec de la modification du pseudo. Veuillez réessayer plus tard.")

def is_owner(ctx):
    return ctx.author.id == bot.owner_id

@bot.command()
@commands.check(is_owner)
async def admin(ctx, member: discord.Member, action: str, count: int):
    print(f"Commande admin exécutée pour {member} avec l'action {action} et le count {count}")  # Débogage

    if member.id not in member_history:
        member_history[member.id] = {"warnings": 0, "bans": 0, "kicks": 0}

    if action.lower() == "warnings":
        member_history[member.id]["warnings"] = count
        await ctx.send(f'Le nombre d\'avertissements de {member.mention} a été mis à jour à {count}.')
    elif action.lower() == "bans":
        member_history[member.id]["bans"] = count
        await ctx.send(f'Le nombre de bannissements de {member.mention} a été mis à jour à {count}.')
    elif action.lower() == "kicks":
        member_history[member.id]["kicks"] = count
        await ctx.send(f'Le nombre de kicks de {member.mention} a été mis à jour à {count}.')
    else:
        await ctx.send("Action non reconnue. Utilisez 'warnings', 'bans' ou 'kicks'.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def kick_voc(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send(f"{member.display_name} n'est pas connecté à un salon vocal.")
        return

    voice_channel = member.voice.channel
    if voice_channel is None:
        await ctx.send(f"{member.display_name} n'est pas connecté à un salon vocal.")
        return

    await member.move_to(None)
    await ctx.send(f"{member.display_name} a été expulsé du salon vocal {voice_channel.name}.")

def can_execute_everywhere(ctx):
    # Autorise l'exécution si l'utilisateur est un administrateur
    return ctx.author.guild_permissions.administrator

@bot.command()
@commands.check_any(commands.check(can_execute_everywhere), commands.is_owner())
async def move(ctx, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice is None:
        await ctx.send(f"{member.display_name} n'est pas connecté à un salon vocal.")
        return

    try:
        await member.move_to(channel)
        await ctx.send(f"{member.display_name} a été déplacé vers le salon vocal {channel.name}.")
    except discord.Forbidden:
        await ctx.send(f"Je n'ai pas les permissions nécessaires pour déplacer {member.display_name}. Veuillez vérifier mes permissions.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite lors du déplacement de {member.display_name}: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Cette commande n'existe pas.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")
    else:
        # Gérer d'autres erreurs
        await ctx.send(f"Une erreur est survenue: {error}")

def is_owner(ctx):
    return ctx.author.id == bot.owner_id

@bot.event
async def on_ready():
    bot.owner_id = (await bot.application_info()).owner.id
    print(f'Bot connecté en tant que {bot.user}')
    print(f'Owner ID: {bot.owner_id}')

@bot.command()
@commands.check(is_owner)
async def shutdown(ctx):
    await ctx.send("Le bot va s'éteindre.")
    await bot.close()

@bot.command()
@commands.check(is_owner)
async def restart(ctx):
    await ctx.send("Le bot va redémarrer.")
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.command(name="role_temp")
@commands.check(is_owner)
async def temp_role(ctx, member: discord.Member, role: discord.Role, duration: int):
    if ctx.guild.owner_id != ctx.author.id:
        await ctx.send("Seul le propriétaire du serveur peut utiliser cette commande.")
        return

    print(f"Commande temp_role exécutée pour {member} avec le rôle {role} pour {duration} secondes")  # Débogage

    await member.add_roles(role)
    await ctx.send(f'{member.mention} a reçu le rôle {role.mention} pour {duration} secondes.')

    await asyncio.sleep(duration)
    await member.remove_roles(role)
    await ctx.send(f'{member.mention} n\'a plus le rôle {role.mention}.')

@bot.command(name="role_set")
@commands.check(is_owner)
async def set_role(ctx, member: discord.Member, role: discord.Role):
    # Vérifier si l'auteur est le propriétaire du serveur
    if ctx.guild.owner_id != ctx.author.id:
        await ctx.send("Seul le propriétaire du serveur peut utiliser cette commande.")
        return

    # Vérifier si le bot a les permissions nécessaires
    bot_role = ctx.guild.me.top_role
    if bot_role <= role:
        await ctx.send("Le rôle spécifié est supérieur ou égal à celui du bot dans la hiérarchie des rôles.")
        return

    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("Le bot n'a pas la permission de gérer les rôles.")
        return

    try:
        # Ajouter le rôle
        await member.add_roles(role)
        await ctx.send(f'{member.mention} a reçu le rôle {role.mention}.')
    except discord.Forbidden:
        await ctx.send("Le bot n'a pas la permission de gérer les rôles pour ce membre.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite : {str(e)}")
        
@bot.event
async def on_message(message):
    # Ne pas répondre à ses propres messages
    if message.author == bot.user:
        return
    
    # Vérifier si le message provient d'un canal ignoré
    if message.channel.id in ignored_channels:
        return
    
    # Ajoutez ici votre logique de traitement des messages
    await bot.process_commands(message)

ignored_channels = [1251163392647892998]
        
bot.run(TOKEN)
