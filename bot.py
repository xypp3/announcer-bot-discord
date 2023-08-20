import os
import discord
from dotenv import load_dotenv
from typing import Optional, List
from discord import Role

load_dotenv()
TOKEN = str(os.getenv("DISCORD_TOKEN"))

intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")

    # get all events and assign roles on startup
    for guild in client.guilds:
        try:
            roles = await guild.fetch_roles()
        except discord.HTTPException:
            raise ValueError("Cannot fetch roles on ready")

        try:
            events = await guild.fetch_scheduled_events()
        except discord.HTTPException:
            raise ValueError("Events cannot be fetched on init")

        try:
            members = guild.fetch_members()
        except (discord.HTTPException, discord.ClientException):
            raise ValueError("Members cannot be fetched on init")

        # prep member data
        id_to_member = {}
        async for member in members:
            id_to_member[member.id] = member

        for e in events:
            role = find_role(e.name, roles)

            # create role if doesn't exist
            if role is None:
                try:
                    role = await guild.create_role(name=e.name, mentionable=True)
                except:
                    raise ValueError("Cannot create role on bot init")

            async for user in e.users():
                member = id_to_member[user.id]
                if member.get_role(role.id) is None:
                    try:
                        await member.add_roles(role)
                        print("added member role")
                    except:
                        raise ValueError("add role to a member")
            # TODO: check if users dict can be null
            #   cause of order of instanticiation and not empty event???


# Create role
@client.event
async def on_scheduled_event_create(event):
    try:
        # TODO: create a random color for group and a funny name
        role = await event.guild.create_role(name=event.name, mentionable=True)

        # add role to member
        member = event.guild.get_member(event.creator_id)
        if member is None:
            raise ValueError("Member not found")

        await member.add_roles(role, reason=f"interested in {event.name}")
    except:
        raise ValueError("cannot create role")
    print(f"create-in::{event.guild.name}::role::{event.name}")


# Delete role
@client.event
async def on_scheduled_event_delete(event):
    try:
        roles = await event.guild.fetch_roles()
        for r in roles:
            if r.name == event.name:
                await r.delete(reason=f"scheduled event {event.name} deleted")
                break
    except:
        raise ValueError("Roles cannot be fetched or deleted")
    print(f"delete-in::{event.guild.name}::event::{event.name}")


# Add user to role
@client.event
async def on_scheduled_event_user_add(event, user):
    # TODO: check the double assign of roles
    #   would happen when you try and add the role to the event creator
    try:
        member = event.guild.get_member(user.id)
        if member is None:
            raise ValueError("Member not found")

        roles = await event.guild.fetch_roles()
        for r in roles:
            if r.name == event.name:
                await member.add_roles(r, reason=f"interested in {event.name}")
    except:
        raise ValueError("Member cannot be added to role")

    print(f"add::{user.name}::to-role::{event.name}")


# Remove user from role
@client.event
async def on_scheduled_event_user_remove(event, user):
    # TODO: check the double remove of roles
    #   could happen when you try and remove the role to the event destroyer
    try:
        member = event.guild.get_member(user.id)
        if member is None:
            raise ValueError("Member not found")

        roles = await event.guild.fetch_roles()
        for r in roles:
            if r.name == event.name:
                await member.remove_roles(r, reason=f"no longer interested in {event.name}")
    except:
        raise ValueError("Member cannot be added to role")

    print(f"remove::{user.name}::to-role::{event.name}")


# TODO: should this be throwable or should this block try, except
def find_role(name: str, roles: List[Role]) -> Optional[Role]:
    for r in roles:
        if name == r.name:
            return r
    return None


if __name__ == "__main__":
    events = []  # event "cache" though might not be necessary
    client.run(TOKEN)
    # TODO:
    #   1. test all things
    #   2. add event for updating scheduled events
    #   3. see if cache?
