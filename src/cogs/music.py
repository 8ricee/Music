from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import discord
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_looping = False
        self.current_url = None
        self.current_quality = '192'
        self.check_empty_channel.start()
        self.check_inactivity.start()

    def cog_unload(self):
        self.check_empty_channel.cancel()
        self.check_inactivity.cancel()

    @tasks.loop(minutes=2)
    async def check_empty_channel(self):
        for vc in self.bot.voice_clients:
            if len(vc.channel.members) == 1:  # Chỉ có bot trong phòng
                await asyncio.sleep(120)  # Chờ 2 phút
                if len(vc.channel.members) == 1:  # Kiểm tra lại
                    await vc.disconnect()
                    channel = vc.channel.guild.system_channel
                    if channel:
                        embed = discord.Embed(
                            title="Disconnected",
                            description=f"Bot has left the channel {vc.channel} due to inactivity.",
                            color=discord.Color.red()
                        )
                        embed.set_footer(text="@8ricee")
                        await channel.send(embed=embed)
                    print(f"Bot has left the channel {vc.channel} in guild {vc.guild.name} (id: {vc.guild.id}) due to inactivity.")

    @tasks.loop(minutes=2)
    async def check_inactivity(self):
        for vc in self.bot.voice_clients:
            if not vc.is_playing() and not vc.is_paused():  # Không có nhạc đang phát hoặc tạm dừng
                await asyncio.sleep(180)  # Chờ 3 phút
                if not vc.is_playing() and not vc.is_paused():  # Kiểm tra lại
                    await vc.disconnect()
                    channel = vc.channel.guild.system_channel
                    if channel:
                        embed = discord.Embed(
                            title="Disconnected",
                            description=f"Bot has left the channel {vc.channel} due to inactivity.",
                            color=discord.Color.red()
                        )
                        embed.set_footer(text="@8ricee")
                        await channel.send(embed=embed)
                    print(f"Bot has left the channel {vc.channel} in guild {vc.guild.name} (id: {vc.guild.id}) due to inactivity.")

    @commands.command()
    async def play(self, ctx, url: str, quality: str = '192'):
        if not ctx.author.voice:
            embed = discord.Embed(
                title="Error",
                description="You need to be in a voice channel to play music!",
                color=discord.Color.red()
            )
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)
            return

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        # Validate quality input
        if quality not in ['64', '128', '192', '256', '320']:
            embed = discord.Embed(
                title="Error",
                description="Invalid quality. Please choose from 64, 128, 192, 256, 320 kbps.",
                color=discord.Color.red()
            )
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)
            return

        self.current_url = url
        self.current_quality = quality

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,  # Sử dụng chất lượng âm thanh do người dùng chọn
            }],
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'  # Bind to IPv4 since IPv6 addresses cause issues sometimes
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn'
                }
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url2, **ffmpeg_options))
                ctx.voice_client.play(source, after=lambda e: asyncio.create_task(self.play_next(ctx)))

            embed = discord.Embed(
                title="Now Playing",
                description=f"[{info['title']}]({url}) at {quality} kbps",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=info['thumbnail'])
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)

            print(f"Now playing: {url} at {quality} kbps in guild {ctx.guild.name} (id: {ctx.guild.id})")
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)
            print(f"An error occurred: {str(e)} in guild {ctx.guild.name} (id: {ctx.guild.id})")

    async def play_next(self, ctx):
        if self.is_looping and self.current_url:
            ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.current_url)), after=lambda e: asyncio.create_task(self.play_next(ctx)))
        else:
            self.current_url = None

    @commands.command()
    async def stop(self, ctx):
        self.is_looping = False
        await ctx.voice_client.disconnect()
        embed = discord.Embed(
            title="Stopped",
            description="Stopped playing music",
            color=discord.Color.red()
        )
        embed.set_footer(text="@8ricee")
        await ctx.send(embed=embed)
        print(f"Stopped playing music in guild {ctx.guild.name} (id: {ctx.guild.id})")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(
                title="Paused",
                description="Paused the music",
                color=discord.Color.orange()
            )
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)
            print(f"Paused the music in guild {ctx.guild.name} (id: {ctx.guild.id})")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(
                title="Resumed",
                description="Resumed the music",
                color=discord.Color.green()
            )
            embed.set_footer(text="@8ricee")
            await ctx.send(embed=embed)
            print(f"Resumed the music in guild {ctx.guild.name} (id: {ctx.guild.id})")

    @commands.command()
    async def loop(self, ctx):
        self.is_looping = not self.is_looping
        status = "enabled" if self.is_looping else "disabled"
        embed = discord.Embed(
            title="Loop",
            description=f"Looping is now {status}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="@8ricee")
        await ctx.send(embed=embed)
        print(f"Looping is now {status} in guild {ctx.guild.name} (id: {ctx.guild.id})")

async def setup(bot):
    await bot.add_cog(Music(bot))