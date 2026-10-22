"""Supabase client configuration and utilities."""

import os

from supabase.lib.client_options import ClientOptions

from supabase import Client, create_client


def get_supabase_client() -> Client | None:
    """
    Get Supabase client instance.

    Returns:
        Supabase client if configured, None otherwise
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        return None

    # Use service role key for backend operations (bypasses RLS)
    # Use anon key for client-side operations (respects RLS)
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    key = service_role_key if service_role_key else supabase_key

    options = ClientOptions(
        auto_refresh_token=True,
        persist_session=True,
    )

    return create_client(supabase_url, key, options=options)


def get_supabase_anon_client() -> Client | None:
    """
    Get Supabase client with anon key (respects RLS).

    Use this for client-side operations where RLS should be enforced.

    Returns:
        Supabase client with anon key if configured, None otherwise
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_anon_key:
        return None

    options = ClientOptions(
        auto_refresh_token=True,
        persist_session=True,
    )

    return create_client(supabase_url, supabase_anon_key, options=options)


def is_supabase_configured() -> bool:
    """
    Check if Supabase is configured.

    Returns:
        True if SUPABASE_URL and at least one key is set
    """
    supabase_url = os.getenv("SUPABASE_URL")
    has_key = bool(os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    return bool(supabase_url and has_key)


def get_supabase_storage_bucket(bucket_name: str = "agent-factory") -> object | None:
    """
    Get Supabase storage bucket.

    Args:
        bucket_name: Name of the storage bucket

    Returns:
        Storage bucket if Supabase is configured, None otherwise
    """
    client = get_supabase_client()
    if not client:
        return None

    return client.storage.from_(bucket_name)
