#!/usr/bin/env python3
import csv
import os
import discord
from discord.ext import commands
from discord import Intents, app_commands
import sqlite3

guild_id = 1160150921301463101

# Declare Intents for the Bot
intents = Intents.default()
intents.messages = True
intents.guilds = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild_id))
    print("Ready!")


# Database setup
def db_setup():
    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS coordinates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x INTEGER,
            y TEXT,
            z INTEGER,
            name TEXT,
            description TEXT,
            added_by TEXT,
            dimension TEXT
        )"""
    )
    conn.commit()
    conn.close()


db_setup()


@tree.command(
    name="help",
    description="Shows help information for commands",
    guild=discord.Object(id=guild_id),
)
async def help(interaction: discord.Interaction):
    # Create an embed for help information
    embed = discord.Embed(
        title="Help - Minecraft Coordinates Bot", color=discord.Color.blue()
    )

    # Add fields for each command
    embed.add_field(
        name="NOTICE",
        value="If you obtain an error while trying to run a command, wait a few seconds, and try again. It might not actually be a problem, and just the bot being annoying.",
        inline=False,
    )
    embed.add_field(
        name="/addcoord",
        value="Add a new Minecraft coordinate. Usage: `/addcoord x:<int> z:<int> name:<str> [y:<str>] [description:<str>] [dimension:<str>]`",
        inline=False,
    )
    embed.add_field(
        name="/listcoords",
        value="List all stored coordinates. Usage: `/listcoords`",
        inline=False,
    )
    embed.add_field(
        name="/updatecoord",
        value="Update an existing coordinate. Usage: `/updatecoord coord_id:<int> [x:<int>] [y:<str>] [z:<int>] [name:<str>] [description:<str>] [dimension:<str>]`",
        inline=False,
    )
    embed.add_field(
        name="/removecoord",
        value="Remove a coordinate. Usage: `/removecoord coord_id:<int>`",
        inline=False,
    )
    embed.add_field(
        name="/find",
        value="Find coordinates based on filters. Usage: `/find [name:<str>] [dimension:<str>] [added_by:<str>]`",
        inline=False,
    )

    # Send the embed to the user's DM
    try:
        await interaction.user.send(embed=embed)
        await interaction.response.send_message(
            "Help information has been sent to your DMs.", ephemeral=True
        )
    except discord.errors.Forbidden:
        # In case the bot can't send DMs to the user
        await interaction.response.send_message(
            "I can't send you a DM. Please check your privacy settings.", ephemeral=True
        )


@tree.command(
    name="addcoord",
    description="Add a Minecraft coordinate",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    x="The X coordinate",
    y="The Y coordinate (optional, defaults to '~')",
    z="The Z coordinate",
    name="Name for this coordinate",
    description="Description of the coordinate (optional)",
    dimension="The dimension (overworld/nether/end)",
)
async def addcoord(
    interaction: discord.Interaction,
    x: int,
    z: int,
    name: str,
    y: str = "~",
    description: str = "",
    dimension: str = "overworld",
):
    user = str(interaction.user)

    # Connect to the SQLite database
    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()

    # Insert the new coordinate into the database
    c.execute(
        "INSERT INTO coordinates (x, y, z, name, description, added_by, dimension) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (x, y, z, name, description, user, dimension),
    )

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Coordinate {name} added successfully.")


@tree.command(
    name="listcoords",
    description="List all Minecraft coordinates",
    guild=discord.Object(id=guild_id),
)
async def listcoords(interaction: discord.Interaction):
    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()
    c.execute("SELECT * FROM coordinates")
    coords = c.fetchall()
    conn.close()

    embed = discord.Embed(title="Minecraft Coordinates", color=discord.Color.blue())

    for coord in coords:
        embed.add_field(
            name=f"ID: {coord[0]} - {coord[4]}",
            value=f"X: {coord[1]}, Y: {coord[2]}, Z: {coord[3]}\nDescription: {coord[5]}\nAdded by: {coord[6]}\nDimension: {coord[7]}",
            inline=False,
        )

    await interaction.response.send_message(embed=embed)


@tree.command(
    name="removecoord",
    description="Remove a Minecraft coordinate",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    coord_id="ID of the coordinate to remove",
)
async def removecoord(interaction: discord.Interaction, coord_id: int):
    # Acknowledge the interaction
    await interaction.response.defer()

    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()

    # Check if the coordinate with the given ID exists
    c.execute("SELECT EXISTS(SELECT 1 FROM coordinates WHERE id=?)", (coord_id,))
    exists = c.fetchone()[0]

    if not exists:
        await interaction.followup.send(f"No coordinate found with ID {coord_id}.")
    else:
        # Proceed with deletion if the record exists
        c.execute("DELETE FROM coordinates WHERE id = ?", (coord_id,))
        conn.commit()
        await interaction.followup.send(
            f"Coordinate with ID {coord_id} removed successfully."
        )

    conn.close()


@tree.command(
    name="updatecoord",
    description="Update a Minecraft coordinate",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    coord_id="ID of the coordinate to update",
    x="The new X coordinate (leave blank to keep current value)",
    y="The new Y coordinate (leave blank to keep current value)",
    z="The new Z coordinate (leave blank to keep current value)",
    name="New name for this coordinate (leave blank to keep current value)",
    description="New description of the coordinate (leave blank to keep current value)",
    dimension="The new dimension (overworld/nether/end, leave blank to keep current value)",
)
async def updatecoord(
    interaction: discord.Interaction,
    coord_id: int,
    x: str = None,
    y: str = None,
    z: str = None,
    name: str = None,
    description: str = None,
    dimension: str = None,
):
    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()

    # Prepare the update statement dynamically based on provided values
    fields_to_update = []
    values = []
    if x is not None:
        fields_to_update.append("x = ?")
        values.append(x)
    if y is not None:
        fields_to_update.append("y = ?")
        values.append(y)
    if z is not None:
        fields_to_update.append("z = ?")
        values.append(z)
    if name is not None:
        fields_to_update.append("name = ?")
        values.append(name)
    if description is not None:
        fields_to_update.append("description = ?")
        values.append(description)
    if dimension is not None:
        fields_to_update.append("dimension = ?")
        values.append(dimension)

    if not fields_to_update:
        await interaction.response.send_message("No updates provided.")
        return

    update_statement = (
        "UPDATE coordinates SET " + ", ".join(fields_to_update) + " WHERE id = ?"
    )
    values.append(coord_id)

    c.execute(update_statement, values)
    conn.commit()
    conn.close()

    await interaction.response.send_message(
        f"Coordinate with ID {coord_id} updated successfully."
    )


@tree.command(
    name="find",
    description="Find Minecraft coordinates based on filters",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    name="Name of the coordinate (optional)",
    dimension="Dimension (overworld/nether/end, optional)",
    added_by="Username of the person who added the coordinate (optional)",
)
async def find(
    interaction: discord.Interaction,
    name: str = None,
    dimension: str = None,
    added_by: str = None,
):
    conn = sqlite3.connect("minecraft_coords.db")
    c = conn.cursor()

    # Prepare the query dynamically based on provided filters
    conditions = []
    values = []
    if name is not None:
        conditions.append("name LIKE ?")
        values.append(f"%{name}%")
    if dimension is not None:
        conditions.append("dimension = ?")
        values.append(dimension)
    if added_by is not None:
        conditions.append("added_by LIKE ?")
        values.append(f"%{added_by}%")

    query = "SELECT * FROM coordinates"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    c.execute(query, values)
    coords = c.fetchall()
    conn.close()

    if not coords:
        await interaction.response.send_message(
            "No coordinates found matching the criteria."
        )
        return

    # Create an embed for the search results
    embed = discord.Embed(title="Search Results", color=discord.Color.blue())
    for coord in coords:
        embed.add_field(
            name=f"ID: {coord[0]}, {coord[4]}",
            value=f"X: {coord[1]}, Y: {coord[2]}, Z: {coord[3]}\nDescription: {coord[5]}\nAdded by: {coord[6]}, Dimension: {coord[7]}",
            inline=False,
        )

    # Send the embed
    await interaction.response.send_message(embed=embed)


client.run("MTE1OTc4MjI4NTA0Njk4MDYzOA.G-wFAw.mdiyBzFp0SOSYe3oTcwB42C3DnKEfJ027J7ZeU")
