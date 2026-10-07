"""
QuantDB Database Direct Connectivity Diagnostics.

Verifies end-to-end connectivity using the same connection layer and environment parameters:
1. DNS hostname resolution
2. TCP port reachability
3. MySQL authentication and SSL transport handshake
4. QuantDB database schema accessibility
5. Execution of 'SELECT 1' test query

Preserves and reports the original MySQL connector exceptions without swallowing.
"""

import os
import socket
import sys
from typing import Any, Dict, Tuple

import mysql.connector
from mysql.connector import Error

from src.database.connection import _get_db_param, _get_ssl_config, get_connection


def run_connectivity_diagnostics(
    host_override: str = None,
    port_override: int = None,
    user_override: str = None,
    password_override: str = None,
    database_override: str = None,
) -> Dict[str, Any]:
    """
    Executes comprehensive 5-stage database connectivity diagnostics.
    Returns a dictionary detailing the outcome of each stage.
    """
    host = host_override or _get_db_param("DB_HOST", "localhost")
    port_val = port_override or int(_get_db_param("DB_PORT", "3306"))
    database = database_override or _get_db_param("DB_NAME", "QuantDB")
    user = user_override or _get_db_param("DB_USER", "root")
    password = password_override if password_override is not None else _get_db_param("DB_PASSWORD", "")

    results: Dict[str, Any] = {
        "config": {
            "host": host,
            "port": port_val,
            "database": database,
            "user": user,
            "password_configured": bool(password),
        },
        "dns_resolution": {"status": "SKIPPED", "ip": None, "error": None},
        "tcp_port": {"status": "SKIPPED", "error": None},
        "mysql_auth_ssl": {"status": "SKIPPED", "cipher": None, "error": None},
        "database_access": {"status": "SKIPPED", "error": None},
        "select_1": {"status": "SKIPPED", "result": None, "error": None},
        "all_passed": False,
    }

    # ---------------------------------------------------------
    # STAGE 1: DNS / HOST RESOLUTION
    # ---------------------------------------------------------
    try:
        ip = socket.gethostbyname(host)
        results["dns_resolution"] = {"status": "PASSED", "ip": ip, "error": None}
    except Exception as e:
        results["dns_resolution"] = {
            "status": "FAILED",
            "ip": None,
            "error": f"DNS resolution failed for '{host}': {e}",
        }
        return results

    # ---------------------------------------------------------
    # STAGE 2: TCP PORT REACHABILITY
    # ---------------------------------------------------------
    try:
        sock = socket.create_connection((host, port_val), timeout=7)
        sock.close()
        results["tcp_port"] = {"status": "PASSED", "error": None}
    except Exception as e:
        results["tcp_port"] = {
            "status": "FAILED",
            "error": f"TCP connection to '{host}:{port_val}' failed: {e}",
        }
        return results

    # ---------------------------------------------------------
    # STAGE 3: MYSQL AUTHENTICATION & SSL TRANSPORT
    # ---------------------------------------------------------
    connect_kwargs = {
        "host": host,
        "port": port_val,
        "database": database,
        "user": user,
        "password": password,
    }
    connect_kwargs.update(_get_ssl_config(host, port_val))

    connection = None
    try:
        connection = mysql.connector.connect(**connect_kwargs)
        if not connection.is_connected():
            results["mysql_auth_ssl"] = {
                "status": "FAILED",
                "error": "mysql.connector.connect returned without active connection status.",
            }
            return results

        ssl_cipher = getattr(connection, "_ssl", {})
        results["mysql_auth_ssl"] = {
            "status": "PASSED",
            "cipher": str(ssl_cipher),
            "error": None,
        }
    except Error as e:
        safe_msg = str(e).replace(password, "******") if password else str(e)
        results["mysql_auth_ssl"] = {
            "status": "FAILED",
            "error": f"MySQL Authentication / SSL Handshake Error: {safe_msg}",
        }
        return results
    except Exception as e:
        safe_msg = str(e).replace(password, "******") if password else str(e)
        results["mysql_auth_ssl"] = {
            "status": "FAILED",
            "error": f"Unexpected Connection Error: {safe_msg}",
        }
        return results

    # ---------------------------------------------------------
    # STAGE 4 & 5: DATABASE ACCESSIBILITY & SELECT 1 QUERY
    # ---------------------------------------------------------
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]
        results["database_access"] = {
            "status": "PASSED",
            "active_database": db_name,
            "error": None,
        }

        cursor.execute("SELECT 1 AS probe;")
        probe_res = cursor.fetchone()[0]
        results["select_1"] = {
            "status": "PASSED",
            "result": probe_res,
            "error": None,
        }

        results["all_passed"] = (probe_res == 1)

    except Error as e:
        safe_msg = str(e).replace(password, "******") if password else str(e)
        results["select_1"] = {
            "status": "FAILED",
            "error": f"Query execution failed: {safe_msg}",
        }
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    return results


def print_diagnostic_report(results: Dict[str, Any]) -> None:
    """Pretty-prints the diagnostic report to console."""
    cfg = results["config"]
    print("=" * 60)
    print("QUANTDB DATABASE CONNECTIVITY DIAGNOSTIC REPORT")
    print("=" * 60)
    print(f"Target Host    : {cfg['host']}")
    print(f"Target Port    : {cfg['port']}")
    print(f"Target Database: {cfg['database']}")
    print(f"Target User    : {cfg['user']}")
    print(f"Password Set   : {cfg['password_configured']}")
    print("-" * 60)

    stages = [
        ("1. DNS Resolution      ", results["dns_resolution"]),
        ("2. TCP Port Connection  ", results["tcp_port"]),
        ("3. MySQL Auth & SSL     ", results["mysql_auth_ssl"]),
        ("4. Database Accessible  ", results["database_access"]),
        ("5. Query 'SELECT 1'     ", results["select_1"]),
    ]

    for label, stage in stages:
        st = stage.get("status")
        icon = "✓" if st == "PASSED" else "✗"
        print(f"[{icon}] {label}: {st}")
        if stage.get("error"):
            print(f"    Reason: {stage['error']}")

    print("=" * 60)
    if results["all_passed"]:
        print("OVERALL STATUS: ALL 5 CONNECTIVITY STAGES PASSED SUCCESSFULLY!")
    else:
        print("OVERALL STATUS: CONNECTIVITY FAILED. SEE STAGE DETAILS ABOVE.")
    print("=" * 60)


if __name__ == "__main__":
    report = run_connectivity_diagnostics()
    print_diagnostic_report(report)
    sys.exit(0 if report["all_passed"] else 1)
