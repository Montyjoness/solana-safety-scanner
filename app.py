import json

import urllib.request

from datetime import datetime, timezone

import streamlit as st

st.set_page_config(

    page_title="Solana Safety Scanner",

    page_icon="🛡️",

    layout="wide"

)

st.title("🛡️ Solana Memecoin Safety Scanner")

st.write("Market data plus deeper on-chain risk signals.")

st.warning(

    "Educational information only. No automated scanner can "

    "guarantee that a token is safe."

)

address = st.text_input(

    "Solana token contract address",

    placeholder="Paste the token address here"

)

if st.button("Scan Token", type="primary"):

    address = address.strip()

    if not address:

        st.error("Please paste a token contract address.")

        st.stop()

    headers = {"User-Agent": "SolanaSafetyScanner/2.0"}

    # Get market information from DEX Screener

    dex_url = (

        "https://api.dexscreener.com/latest/dex/tokens/"

        + address

    )

    try:

        with st.spinner("Checking market and on-chain risks..."):

            request = urllib.request.Request(

                dex_url,

                headers=headers

            )

            with urllib.request.urlopen(

                request,

                timeout=15

            ) as response:

                dex_data = json.loads(response.read().decode())

    except Exception:

        st.error(

            "Market information could not be retrieved. "

            "Check the address and try again."

        )

        st.stop()

    pairs = [

        pair for pair in (dex_data.get("pairs") or [])

        if pair.get("chainId") == "solana"

    ]

    if not pairs:

        st.error("No Solana trading pair was found.")

        st.stop()

    pair = max(

        pairs,

        key=lambda item: float(

            (item.get("liquidity") or {}).get("usd") or 0

        )

    )

    liquidity = float(

        (pair.get("liquidity") or {}).get("usd") or 0

    )

    market_cap = float(

        pair.get("marketCap") or pair.get("fdv") or 0

    )

    volume = float(

        (pair.get("volume") or {}).get("h24") or 0

    )

    buys = int(

        ((pair.get("txns") or {}).get("h24") or {})

        .get("buys") or 0

    )

    sells = int(

        ((pair.get("txns") or {}).get("h24") or {})

        .get("sells") or 0

    )

    change = float(

        (pair.get("priceChange") or {}).get("h24") or 0

    )

    price = float(pair.get("priceUsd") or 0)

    created_ms = pair.get("pairCreatedAt")

    age_hours = None

    if created_ms:

        created = datetime.fromtimestamp(

            created_ms / 1000,

            timezone.utc

        )

        age_hours = (

            datetime.now(timezone.utc) - created

        ).total_seconds() / 3600

    score = 0

    market_warnings = []

    if liquidity < 10000:

        score += 35

        market_warnings.append(

            "Critical: Liquidity is below $10,000"

        )

    elif liquidity < 25000:

        score += 25

        market_warnings.append(

            "High: Liquidity is below $25,000"

        )

    elif liquidity < 50000:

        score += 12

        market_warnings.append(

            "Caution: Liquidity is below $50,000"

        )

    if market_cap and liquidity / market_cap < 0.05:

        score += 20

        market_warnings.append(

            "High: Liquidity is under 5% of market cap"

        )

    elif market_cap and liquidity / market_cap < 0.10:

        score += 10

        market_warnings.append(

            "Caution: Liquidity is under 10% of market cap"

        )

    if volume < 5000:

        score += 15

        market_warnings.append(

            "Caution: Very low 24-hour volume"

        )

    if sells > buys * 1.5 and sells >= 10:

        score += 15

        market_warnings.append(

            "High: Sells greatly exceed buys"

        )

    if change > 150:

        score += 15

        market_warnings.append(

            "Caution: Price rose over 150% in 24 hours"

        )

    if age_hours is not None and age_hours < 6:

        score += 15

        market_warnings.append(

            "High: Trading pair is less than 6 hours old"

        )

    elif age_hours is not None and age_hours < 24:

        score += 8

        market_warnings.append(

            "Caution: Trading pair is less than 24 hours old"

        )

    # Get deeper on-chain warnings from RugCheck

    rugcheck_available = False

    onchain_warnings = []

    rug_url = (

        "https://api.rugcheck.xyz/v1/tokens/"

        + address

        + "/report/summary"

    )

    try:

        rug_request = urllib.request.Request(

            rug_url,

            headers=headers

        )

        with urllib.request.urlopen(

            rug_request,

            timeout=20

        ) as response:

            rug_data = json.loads(response.read().decode())

        rugcheck_available = True

        token_meta = rug_data.get("tokenMeta") or {}

        top_holders = rug_data.get("topHolders") or []

        top10_holder_pct = 0.0

        if top_holders:

        top10_holder_pct = sum(

        float(holder.get("pct", 0) or 0)

        for holder in top_holders[:10]
        )
        if top10_holder_pct >= 70:
        
        score += 30
        
        onchain_warnings.append(
        
            f"CRITICAL: Top 10 holders control {top10_holder_pct:.1f}% of supply"
        
        )
        
        elif top10_holder_pct >= 50:
        
            score += 20
            
            onchain_warnings.append(
            
                f"HIGH: Top 10 holders control {top10_holder_pct:.1f}% of supply"
            
            )
        
        elif top10_holder_pct >= 30:
        
            score += 10
            
            onchain_warnings.append(
            
                f"CAUTION: Top 10 holders control {top10_holder_pct:.1f}% of supply"
            
        )
        risks = rug_data.get("risks") or []

        for risk in risks:

            name = str(risk.get("name") or "On-chain warning")

            description = str(risk.get("description") or "")

            level = str(risk.get("level") or "warning").lower()

            if level in ("danger", "critical"):

                score += 12

            elif level in ("warn", "warning"):

                score += 6

            else:

                score += 3

            if description:

                onchain_warnings.append(

                    f"{level.upper()}: {name} — {description}"

                )

            else:

                onchain_warnings.append(

                    f"{level.upper()}: {name}"

                )

    except Exception:

        rugcheck_available = False

    score = min(score, 100)

    if score >= 70:

        rating = "EXTREME RISK — AVOID"

        color = "red"

    elif score >= 45:

        rating = "HIGH RISK"

        color = "red"

    elif score >= 20:

        rating = "MEDIUM RISK"

        color = "orange"

    else:

        rating = "LOWER DETECTED RISK"

        color = "green"

    token = pair.get("baseToken") or {}

    token_name = token.get("name", "Unknown")

    symbol = token.get("symbol", "Unknown")

    st.divider()

    st.subheader(f"{token_name} ({symbol})")

    st.markdown(

        f"### Risk score: :{color}[{score}/100 — {rating}]"

    )

    st.progress(score)

    col1, col2, col3 = st.columns(3)

    col1.metric("Price", f"${price:,.10f}")

    col2.metric("Market Cap / FDV", f"${market_cap:,.0f}")

    col3.metric("Liquidity", f"${liquidity:,.0f}")

    col1.metric("24H Volume", f"${volume:,.0f}")

    col2.metric("24H Buys", f"{buys:,}")

    col3.metric("24H Sells", f"{sells:,}")

    st.metric("24H Price Change", f"{change:,.1f}%")

    if age_hours is not None:

        st.write(

            f"Trading-pair age: **{age_hours:,.1f} hours**"

        )

    st.subheader("Market warnings")

    if market_warnings:

        for warning in market_warnings:

            st.warning(warning)

    else:

        st.success("No basic market warnings were detected.")

    st.subheader("On-chain safety warnings")

    if not rugcheck_available:

        st.error(

            "On-chain information is unavailable. "

            "Treat these checks as UNKNOWN, not safe."

        )

    elif onchain_warnings:

        for warning in onchain_warnings:

            st.error(warning)

    else:

        st.success(

            "No on-chain warnings were returned by the provider."

        )

    st.caption(

        "The score is an automated estimate based on available "

        "market and on-chain data. Missing data is never proof "

        "that a token is safe."

    )

    pair_url = pair.get("url")

    if pair_url:

        st.link_button("Open on DEX Screener", pair_url)

    st.link_button(

        "View Full RugCheck Report",

        "https://rugcheck.xyz/tokens/" + address

    )
