"""CLI tool for managing test data in Postgres."""

import random
import string
from datetime import datetime
from typing import Optional

import click
import psycopg2
from psycopg2.extras import RealDictCursor
from rich.console import Console
from rich.table import Table

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)
console = Console()


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
    )


def generate_random_email() -> str:
    """Generate a random email address."""
    username = "".join(random.choices(string.ascii_lowercase, k=8))
    domain = random.choice(["example.com", "test.com", "demo.org"])
    return f"{username}@{domain}"


def generate_random_name() -> str:
    """Generate a random name."""
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


@click.group()
def cli():
    """CDC Test Data Management CLI."""
    pass


@cli.command()
@click.option("--email", "-e", help="User email address")
@click.option("--name", "-n", help="User full name")
@click.option("--age", "-a", type=int, help="User age")
@click.option("--status", "-s", default="active", help="User status (default: active)")
@click.option("--random", "-r", is_flag=True, help="Generate random user data")
def add(email: Optional[str], name: Optional[str], age: Optional[int], status: str, random: bool):
    """Add a new user to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if random:
            email = email or generate_random_email()
            name = name or generate_random_name()
            age = age or random.randint(18, 80)

        if not email or not name:
            console.print("[red]Error: Email and name are required (or use --random flag)[/red]")
            return

        # Insert user
        insert_query = """
            INSERT INTO users (email, name, age, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, name, age, status, created_at, updated_at
        """
        cursor.execute(insert_query, (email, name, age, status))
        result = cursor.fetchone()

        conn.commit()

        # Display result
        table = Table(title="User Added")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("ID", str(result[0]))
        table.add_row("Email", result[1])
        table.add_row("Name", result[2])
        table.add_row("Age", str(result[3]) if result[3] else "N/A")
        table.add_row("Status", result[4])
        table.add_row("Created At", str(result[5]))
        table.add_row("Updated At", str(result[6]))

        console.print(table)
        console.print(f"[green]✓ User added successfully! CDC event should be captured by Debezium.[/green]")

        cursor.close()
        conn.close()

    except psycopg2.IntegrityError as e:
        console.print(f"[red]Error: User with email '{email}' already exists[/red]")
        logger.error(f"Database integrity error: {e}")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error adding user: {e}", exc_info=True)


@cli.command()
@click.option("--id", "-i", type=int, help="User ID to update")
@click.option("--email", "-e", help="New email address")
@click.option("--name", "-n", help="New name")
@click.option("--age", "-a", type=int, help="New age")
@click.option("--status", "-s", help="New status")
def update(id: Optional[int], email: Optional[str], name: Optional[str], age: Optional[int], status: Optional[str]):
    """Update an existing user."""
    if not id:
        console.print("[red]Error: User ID is required[/red]")
        return

    updates = {}
    if email:
        updates["email"] = email
    if name:
        updates["name"] = name
    if age is not None:
        updates["age"] = age
    if status:
        updates["status"] = status

    if not updates:
        console.print("[red]Error: At least one field to update is required[/red]")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update query
        set_clauses = [f"{key} = %s" for key in updates.keys()]
        update_query = f"""
            UPDATE users
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING id, email, name, age, status, created_at, updated_at
        """
        cursor.execute(update_query, list(updates.values()) + [id])

        if cursor.rowcount == 0:
            console.print(f"[red]Error: User with ID {id} not found[/red]")
            return

        result = cursor.fetchone()
        conn.commit()

        # Display result
        table = Table(title="User Updated")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("ID", str(result[0]))
        table.add_row("Email", result[1])
        table.add_row("Name", result[2])
        table.add_row("Age", str(result[3]) if result[3] else "N/A")
        table.add_row("Status", result[4])
        table.add_row("Created At", str(result[5]))
        table.add_row("Updated At", str(result[6]))

        console.print(table)
        console.print(f"[green]✓ User updated successfully! CDC event should be captured by Debezium.[/green]")

        cursor.close()
        conn.close()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error updating user: {e}", exc_info=True)


@cli.command()
@click.option("--id", "-i", type=int, help="User ID to delete")
def delete(id: Optional[int]):
    """Delete a user from the database."""
    if not id:
        console.print("[red]Error: User ID is required[/red]")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user info before deletion
        cursor.execute("SELECT id, email, name FROM users WHERE id = %s", (id,))
        user = cursor.fetchone()

        if not user:
            console.print(f"[red]Error: User with ID {id} not found[/red]")
            return

        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()

        console.print(f"[green]✓ User deleted successfully! (ID: {user[0]}, Email: {user[1]}, Name: {user[2]})[/green]")
        console.print(f"[green]CDC event should be captured by Debezium.[/green]")

        cursor.close()
        conn.close()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error deleting user: {e}", exc_info=True)


@cli.command()
@click.option("--limit", "-l", type=int, default=10, help="Number of users to display")
def list(limit: int):
    """List users in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, email, name, age, status, created_at, updated_at FROM users ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        users = cursor.fetchall()

        if not users:
            console.print("[yellow]No users found in the database[/yellow]")
            return

        table = Table(title=f"Users (showing {len(users)} of {limit})")
        table.add_column("ID", style="cyan")
        table.add_column("Email", style="green")
        table.add_column("Name", style="yellow")
        table.add_column("Age", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("Created At", style="white")

        for user in users:
            table.add_row(
                str(user["id"]),
                user["email"],
                user["name"],
                str(user["age"]) if user["age"] else "N/A",
                user["status"],
                str(user["created_at"]),
            )

        console.print(table)

        cursor.close()
        conn.close()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Error listing users: {e}", exc_info=True)


@cli.command()
@click.option("--count", "-c", type=int, default=5, help="Number of random users to generate")
def generate(count: int):
    """Generate multiple random users."""
    console.print(f"[cyan]Generating {count} random users...[/cyan]")

    for i in range(count):
        email = generate_random_email()
        name = generate_random_name()
        age = random.randint(18, 80)
        status = random.choice(["active", "active", "active", "inactive"])  # Bias towards active

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, name, age, status) VALUES (%s, %s, %s, %s)",
                (email, name, age, status),
            )
            conn.commit()
            cursor.close()
            conn.close()
            console.print(f"[green]✓ Created user {i+1}/{count}: {email}[/green]")
        except psycopg2.IntegrityError:
            console.print(f"[yellow]⚠ Skipped duplicate email: {email}[/yellow]")
        except Exception as e:
            console.print(f"[red]Error creating user: {e}[/red]")

    console.print(f"[green]✓ Generated {count} users! CDC events should be captured by Debezium.[/green]")


if __name__ == "__main__":
    cli()

