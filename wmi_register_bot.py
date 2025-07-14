import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1387102987238768783  # Replace with your actual server ID
ROLE_STUDENT = 1392653369964757154
LOG_CHANNEL_ID = 1392655742430871754
INVITE_LINK = "https://discord.gg/66qx29Tf"

pending_roles = {}

# Modal for WMI Registration
class RegistrationModal(discord.ui.Modal, title="🌸 WMI Registration"):
    name = discord.ui.TextInput(label="Full Name", placeholder="e.g. Elira Q.", required=True)
    email = discord.ui.TextInput(label="Email (Optional)", placeholder="elira@example.com", required=False)
    notes = discord.ui.TextInput(label="Optional Notes", placeholder="Anything else?", required=False, style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌸 Registration Complete",
            description="Please confirm your role below to finish your registration!",
            color=0xD8BFD8
        )
        embed.add_field(name="Full Name", value=self.name.value, inline=True)
        embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
        if self.email.value:
            embed.add_field(name="Email", value=self.email.value, inline=True)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        await interaction.response.send_message(embed=embed, view=RoleSelectionView(self.name.value, self.email.value, self.notes.value, interaction.user), ephemeral=True)

# View for selecting the student role
class RoleSelectionView(discord.ui.View):
    def __init__(self, name, email, notes, user):
        super().__init__(timeout=120)
        self.name = name
        self.email = email
        self.notes = notes
        self.user = user

    @discord.ui.button(label="🎓 MS1 - First Year Student", style=discord.ButtonStyle.primary)
    async def assign_student(self, interaction: discord.Interaction, button: discord.ui.Button):
        pending_roles[self.user.id] = ROLE_STUDENT
        guild = interaction.guild
        member = guild.get_member(self.user.id)

        if member:
            role = guild.get_role(ROLE_STUDENT)
            if role:
                await member.add_roles(role)
                await interaction.response.send_message("🎉 Role assigned! Welcome to MS1!", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Role not found.", ephemeral=True)
        else:
            await interaction.response.send_message("📨 Please join the main server first: " + INVITE_LINK, ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log = discord.Embed(title="📋 New Student Registered", color=discord.Color.purple())
            log.add_field(name="Name", value=self.name, inline=True)
            log.add_field(name="Discord", value=self.user.mention, inline=True)
            if self.email:
                log.add_field(name="Email", value=self.email, inline=True)
            log.add_field(name="Role", value="MS1 - First Year Student", inline=True)
            if self.notes:
                log.add_field(name="Notes", value=self.notes, inline=False)
            await log_channel.send(embed=log)

# Slash command to start registration
@bot.tree.command(name="wmi_register", description="Register for Wisteria Medical Institute")
async def wmi_register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

# Assign role automatically when a user joins
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    role_id = pending_roles.get(member.id)
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(f"✅ {member.mention} was auto-assigned MS1 role.")

# Sync and log in
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced commands to guild {GUILD_ID}")
    except Exception as e:
        print("❌ Failed to sync commands:", e)
    print(f"🟣 Logged in as {bot.user}")

# Health check for Seenode
async def handle(request):
    return web.Response(text="🌸 WMI Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server running on port {port}")

async def main():
    await bot.login(os.getenv("DISCORD_TOKEN"))
    await start_webserver()
    await bot.connect()

if __name__ == "__main__":
    asyncio.run(main())
