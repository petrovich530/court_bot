import disnake
from disnake.ext import commands
from disnake.ui import Modal, TextInput, Button, View

# Идентификаторы категорий и канала
COURT_CATEGORY_ID = #канал, в котором можно подать иск
ACTIVE_CASES_CATEGORY_ID = #открыть
CLOSED_CASES_CATEGORY_ID = #закрыть
ADMIN_ROLE_ID = #роль адм/тех, у кого постоянный доступ к искам
SUBMIT_CASE_CHANNEL_ID =   # Канал для подачи исков

intents = disnake.Intents.all()

bot = commands.InteractionBot(intents=intents, activity=disnake.Game(name="Суд"))

class CaseSubmissionModal(Modal):
    def __init__(self):
        components = [
            TextInput(
                label="Название иска",
                placeholder="Введите название иска",
                custom_id="case_title",
                style=disnake.TextInputStyle.short
            ),
            TextInput(
                label="ID ответчика",
                placeholder="Введите ID ответчика",
                custom_id="defendant_id",
                style=disnake.TextInputStyle.short
            ),
            TextInput(
                label="Описание иска",
                placeholder="Введите описание",
                custom_id="case_description",
                style=disnake.TextInputStyle.paragraph
            ),
            TextInput(
                label="Дополнительная информация",
                placeholder="Введите дополнительную информацию",
                custom_id="additional_info",
                style=disnake.TextInputStyle.paragraph,
                required=False
            )
        ]
        super().__init__(title="Подача иска", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        # Извлечение данных из modal input
        case_title = interaction.text_values["case_title"]
        defendant_id = int(interaction.text_values["defendant_id"])  # Извлекаем ID ответчика
        case_description = interaction.text_values["case_description"]
        additional_info = interaction.text_values.get("additional_info", "")

        # Поиск ответчика по ID
        defendant_member = interaction.guild.get_member(defendant_id)

        # Создание канала для иска
        category = disnake.utils.get(interaction.guild.categories, id=ACTIVE_CASES_CATEGORY_ID)
        case_channel = await interaction.guild.create_text_channel(name=f'иск-{case_title}', category=category)

        # Создание embed с информацией об иске
        embed = disnake.Embed(title=f"Иск: {case_title}", description=case_description, color=0x00ff00)
        embed.add_field(name="Ответчик", value=f"<@{defendant_id}>")
        if additional_info:
            embed.add_field(name="Дополнительная информация", value=additional_info)

        # Отправка сообщения с упоминанием
        mention_message = f"{interaction.author.mention} подал иск против {defendant_member.mention}."
        await case_channel.send(content=mention_message, embed=embed)

        # Сообщение о возможности загрузки файлов
        await case_channel.send(f"{interaction.author.mention}, вы можете загрузить скриншоты или дополнительные файлы.")

        # Добавление кнопки "Закрыть иск"
        view = CloseCaseView(case_channel, defendant_member, interaction.author)
        await case_channel.send(view=view)

        # Установка разрешений на канал
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)  # Получаем роль админа
        if admin_role:
            await case_channel.set_permissions(admin_role, read_messages=True, send_messages=True)

        await case_channel.set_permissions(interaction.author, read_messages=True, send_messages=True)
        if defendant_member:
            await case_channel.set_permissions(defendant_member, read_messages=True, send_messages=True)

        # Отправка подтверждения пользователю
        await interaction.response.send_message(f"Иск подан успешно. Канал создан: {case_channel.mention}", ephemeral=True)
class CloseCaseView(View):
    def __init__(self, case_channel, defendant_member, author):
        super().__init__(timeout=None)
        self.case_channel = case_channel
        self.defendant_member = defendant_member
        self.author = author

    @disnake.ui.button(label="Закрыть иск", style=disnake.ButtonStyle.danger)
    async def close_case(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        closed_category = disnake.utils.get(interaction.guild.categories, id=CLOSED_CASES_CATEGORY_ID)
        await self.case_channel.edit(category=closed_category)
        await self.case_channel.send("Иск был закрыт и перемещен в архив.")
        
        # Удаляем доступ к каналу
        await self.case_channel.set_permissions(self.author, overwrite=None)
        if self.defendant_member:
            await self.case_channel.set_permissions(self.defendant_member, overwrite=None)

        await interaction.response.send_message("Иск закрыт.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен и готов к работе!')

@bot.slash_command(description="Подать иск в суд")
async def lawsuit(interaction: disnake.ApplicationCommandInteraction):
    # Проверяем, в правильном ли канале была вызвана команда
    if interaction.channel.id != SUBMIT_CASE_CHANNEL_ID:
        await interaction.response.send_message("Вы можете подать иск только в канале, предназначенном для подачи исков.", ephemeral=True)
        return

    modal = CaseSubmissionModal()
    await interaction.response.send_modal(modal)

bot.run(токен)
