import duckdb


def get_connection(database=":memory:"):
    """
    Return a DuckDB connection with the spatial extension loaded.

    The extension is installed automatically on first use and
    reused on subsequent connections.
    """
    con = duckdb.connect(database)

    try:
        try:
            con.execute("LOAD spatial;")
        except duckdb.Error:
            # First-time setup: download/install the extension.
            con.execute("INSTALL spatial;")
            con.execute("LOAD spatial;")

        return con

    except Exception as exc:
        con.close()
        raise RuntimeError(
            "Unable to initialize DuckDB spatial support. "
            "Check network connectivity and DuckDB installation."
        ) from exc
