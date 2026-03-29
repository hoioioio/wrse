use pyo3::prelude::*;

fn apply_slip(price: f64, side: &str, slip_bps: f64) -> f64 {
    let slip = slip_bps / 10000.0;
    if side == "buy" {
        price * (1.0 + slip)
    } else {
        price * (1.0 - slip)
    }
}

fn fee_cost(notional: f64, fee_rate: f64) -> f64 {
    notional.abs() * fee_rate
}

fn funding_pnl_per_bar(side: &str, funding_rate: f64, notional: f64, bar_hours: f64, funding_hours: f64) -> f64 {
    let mult = if side == "buy" { -1.0 } else { 1.0 };
    mult * funding_rate * notional * (bar_hours / funding_hours)
}

fn est_spread_bps(close: f64, high: f64, low: f64, l2_spread_bps: Option<f64>) -> f64 {
    if let Some(v) = l2_spread_bps {
        if v.is_finite() && v > 0.0 {
            return v;
        }
    }
    if close <= 0.0 {
        return 2.0;
    }
    let rng_bps = ((high - low) / close) * 10000.0;
    let mut v = rng_bps * 0.08;
    if v < 1.0 {
        v = 1.0;
    }
    if v > 15.0 {
        v = 15.0;
    }
    v
}

fn exec_price_impl(
    side: &str,
    open_px: f64,
    bar_high: f64,
    bar_low: f64,
    shock_score: f64,
    close: f64,
    high: f64,
    low: f64,
    l2_spread_bps: Option<f64>,
    l2_micro_dev_bps: Option<f64>,
    l2_imb: Option<f64>,
    slip_bps: f64,
    exec_mode: &str,
    maker_fee_rate: f64,
    taker_fee_rate: f64,
    maker_base_offset_bps: f64,
    maker_spread_mult: f64,
    maker_micro_mult: f64,
    maker_imb_mult: f64,
    shock_aggr_th: f64,
) -> (f64, f64, bool) {
    if shock_score.abs() >= shock_aggr_th || exec_mode.to_lowercase() == "taker" {
        let px = apply_slip(open_px, side, slip_bps);
        return (px, taker_fee_rate, true);
    }

    let spread_bps = est_spread_bps(close, high, low, l2_spread_bps);
    let micro_dev = l2_micro_dev_bps.unwrap_or(0.0);
    let imb = l2_imb.unwrap_or(0.0);

    let side_sign = if side == "buy" { 1.0 } else { -1.0 };
    let mut offset_bps = maker_base_offset_bps + maker_spread_mult * spread_bps;
    offset_bps -= maker_micro_mult * (side_sign * micro_dev);
    offset_bps -= maker_imb_mult * (side_sign * imb);

    let max_off = (spread_bps * 2.5).max(2.0);
    if offset_bps < 0.0 {
        offset_bps = 0.0;
    }
    if offset_bps > max_off {
        offset_bps = max_off;
    }

    let limit_px = open_px * (1.0 - side_sign * (offset_bps / 10000.0));
    let touched = if side == "buy" { bar_low <= limit_px } else { bar_high >= limit_px };
    if touched {
        return (limit_px, maker_fee_rate, true);
    }
    if exec_mode.to_lowercase() == "maker_then_taker" {
        let px = apply_slip(open_px, side, slip_bps);
        return (px, taker_fee_rate, true);
    }
    (f64::NAN, 0.0, false)
}

#[pyfunction]
fn exec_price_rust(
    side: &str,
    open_px: f64,
    bar_high: f64,
    bar_low: f64,
    shock_score: f64,
    close: f64,
    high: f64,
    low: f64,
    l2_spread_bps: Option<f64>,
    l2_micro_dev_bps: Option<f64>,
    l2_imb: Option<f64>,
    slip_bps: f64,
    exec_mode: &str,
    maker_fee_rate: f64,
    taker_fee_rate: f64,
    maker_base_offset_bps: f64,
    maker_spread_mult: f64,
    maker_micro_mult: f64,
    maker_imb_mult: f64,
    shock_aggr_th: f64,
) -> (f64, f64, bool) {
    exec_price_impl(
        side,
        open_px,
        bar_high,
        bar_low,
        shock_score,
        close,
        high,
        low,
        l2_spread_bps,
        l2_micro_dev_bps,
        l2_imb,
        slip_bps,
        exec_mode,
        maker_fee_rate,
        taker_fee_rate,
        maker_base_offset_bps,
        maker_spread_mult,
        maker_micro_mult,
        maker_imb_mult,
        shock_aggr_th,
    )
}

#[pyfunction]
fn fee_cost_rust(notional: f64, fee_rate: f64) -> f64 {
    fee_cost(notional, fee_rate)
}

#[pyfunction]
fn funding_pnl_per_bar_rust(side: &str, funding_rate: f64, notional: f64, bar_hours: f64, funding_hours: f64) -> f64 {
    funding_pnl_per_bar(side, funding_rate, notional, bar_hours, funding_hours)
}

#[pymodule]
fn wrse_rust(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(exec_price_rust, m)?)?;
    m.add_function(wrap_pyfunction!(fee_cost_rust, m)?)?;
    m.add_function(wrap_pyfunction!(funding_pnl_per_bar_rust, m)?)?;
    Ok(())
}
