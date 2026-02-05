# -*- coding: utf-8 -*-
"""
Helper functions for Quality Control Capacity Calculation
"""

import pandas as pd
import math
import logging

logger = logging.getLogger(__name__)


def calculate_quality_control_capacity(
    df_giao_kho_filtered,
    df_shift_schedule,
    df_hr_daily_head_counts,
    df_thoi_gian_hoan_thanh,
    selected_date
):
    """
    Tính toán Công Suất Kiểm Tra
    
    Returns:
        dict: {
            'cs_tong': float,
            'A': int,
            'B': float,
            'thoi_gian_100_nguoi': float,
            'total_completion_time': float
        }
    """
    
    # Default values
    result = {
        'cs_tong': 0,
        'cs_truc_tiep': 0,
        'A_tong': 0,
        'A_truc_tiep': 0,
        'B_tong': 0,
        'practical_employees_count': 0,
        'thoi_gian_100_nguoi': 0,
        'thoi_gian_nguoi_truc_tiep': 0,
        'total_completion_time': 0
    }
    
    if df_shift_schedule is None or df_shift_schedule.empty:
        return result
    if df_hr_daily_head_counts is None or df_hr_daily_head_counts.empty:
        return result
    if df_thoi_gian_hoan_thanh is None or df_thoi_gian_hoan_thanh.empty:
        return result
    if df_giao_kho_filtered is None or df_giao_kho_filtered.empty:
        return result
    
    # Parse selected date
    if selected_date == 'Tất cả':
        return result  # Cannot calculate for "All dates"
    
    test_date_parsed = pd.to_datetime(selected_date, format='%d/%m/%Y')
    
    # ============= Calculate A for CS Tổng and CS Trực Tiếp =============
    # tong_sl_nsu_dangky_lam_12h: Total 12h workers (for CS Tổng)
    # tong_sl_nsu_tructiep_lam_12h: Direct 12h workers only (for CS Trực Tiếp)
    
    tong_sl_nsu_dangky_lam_12h = 0
    tong_sl_nsu_tructiep_lam_12h = 0
    
    # To-Do: do the same with these following columns:
    tong_sl_nsu_dangky_lam_8h = 0
    tong_sl_nsu_tructiep_lam_8h = 0
    
    df_hr_filtered = df_hr_daily_head_counts[
        (df_hr_daily_head_counts['Department ID'] == '0300_BPKT') &
        (df_hr_daily_head_counts['Working Date Parsed'] == test_date_parsed)
    ].copy()
    
    if len(df_hr_filtered) > 0:
        # Get tong_sl_nsu_dangky_lam_12h from "Tong So Nguoi Lam Them Gio 12h" (total 12h workers)
        if 'Tong So Nguoi Lam Them Gio 12h' in df_hr_filtered.columns:
            tong_sl_nsu_dangky_lam_12h_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 12h'].iloc[0]).strip()
            if tong_sl_nsu_dangky_lam_12h_str and tong_sl_nsu_dangky_lam_12h_str != '' and tong_sl_nsu_dangky_lam_12h_str != 'nan':
                try:
                    tong_sl_nsu_dangky_lam_12h = int(float(tong_sl_nsu_dangky_lam_12h_str.replace(',', '.')))
                except (ValueError, TypeError):
                    logger.debug("Invalid number for Tong So Nguoi Lam Them Gio 12h: %r", tong_sl_nsu_dangky_lam_12h_str)
                    tong_sl_nsu_dangky_lam_12h = 0
        
        # Get tong_sl_nsu_tructiep_lam_12h from "Tong So Nguoi Lam Them Gio 12h Truc Tiep" (direct 12h workers)
        if 'Tong So Nguoi Lam Them Gio 12h Truc Tiep' in df_hr_filtered.columns:
            tong_sl_nsu_tructiep_lam_12h_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 12h Truc Tiep'].iloc[0]).strip()
            if tong_sl_nsu_tructiep_lam_12h_str and tong_sl_nsu_tructiep_lam_12h_str != '' and tong_sl_nsu_tructiep_lam_12h_str != 'nan':
                try:
                    tong_sl_nsu_tructiep_lam_12h = int(float(tong_sl_nsu_tructiep_lam_12h_str.replace(',', '.')))
                except (ValueError, TypeError):
                    logger.debug("Invalid number for Tong So Nguoi Lam Them Gio 12h Truc Tiep: %r", tong_sl_nsu_tructiep_lam_12h_str)
                    tong_sl_nsu_tructiep_lam_12h = 0
                    
        if 'Tong So Nguoi Lam Them Gio 8h' in df_hr_filtered.columns:
            tong_sl_nsu_dangky_lam_8h_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 8h'].iloc[0]).strip()
            if tong_sl_nsu_dangky_lam_8h_str and tong_sl_nsu_dangky_lam_8h_str != '' and tong_sl_nsu_dangky_lam_8h_str != 'nan':
                try:
                    tong_sl_nsu_dangky_lam_8h = int(float(tong_sl_nsu_dangky_lam_8h_str.replace(',', '.')))
                except (ValueError, TypeError):
                    logger.debug("Invalid number for Tong So Nguoi Lam Them Gio 8h: %r", tong_sl_nsu_dangky_lam_8h_str)
                    tong_sl_nsu_dangky_lam_8h = 0
                    
        if 'Tong So Nguoi Lam Them Gio 8h Truc Tiep' in df_hr_filtered.columns:
            tong_sl_nsu_tructiep_lam_8h_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 8h Truc Tiep'].iloc[0]).strip()
            if tong_sl_nsu_tructiep_lam_8h_str and tong_sl_nsu_tructiep_lam_8h_str != '' and tong_sl_nsu_tructiep_lam_8h_str != 'nan':
                try:
                    tong_sl_nsu_tructiep_lam_8h = int(float(tong_sl_nsu_tructiep_lam_8h_str.replace(',', '.')))
                except (ValueError, TypeError):
                    logger.debug("Invalid number for Tong So Nguoi Lam Them Gio 8h Truc Tiep: %r", tong_sl_nsu_tructiep_lam_8h_str)
                    tong_sl_nsu_tructiep_lam_8h = 0
    
    # ============= Calculate 100-person time (for CS Tổng) =============
    tong_thoi_gian_nang_luc_du_kien = (tong_sl_nsu_dangky_lam_12h * 10 * 60) + (tong_sl_nsu_dangky_lam_8h * 6.5 * 60)
    
    # ============= Calculate total completion time =============
    total_completion_time = 0
    
    for _, row in df_giao_kho_filtered.iterrows():
        ten_chi_tiet = row['ten_chi_tiet']
        sll_str = str(row.get('sll', '')).replace(',', '.')
        try:
            sll = float(sll_str)
        except (ValueError, TypeError):
            logger.debug("Skipping row with invalid sll=%r for ten_chi_tiet=%r", sll_str, row.get('ten_chi_tiet'))
            continue
        if not math.isfinite(sll):
            logger.debug("Skipping row with non-finite sll=%r for ten_chi_tiet=%r", sll, row.get('ten_chi_tiet'))
            continue
        
        # Find matching time data
        df_time_match = df_thoi_gian_hoan_thanh[
            df_thoi_gian_hoan_thanh['ten_chi_tiet'] == ten_chi_tiet
        ].copy()
        
        if len(df_time_match) == 0:
            continue
        
        # Extract PKT codes
        def get_time_value(code):
            subset = df_time_match[df_time_match['ma_cv'] == code]['Thoi_Gian']
            if subset.empty:
                return 0.0
            val = subset.iloc[0]
            try:
                return float(str(val).replace(',', '.'))
            except (ValueError, TypeError):
                logger.debug("Invalid Thoi_Gian for code=%s ten_chi_tiet=%s: %r", code, ten_chi_tiet, val)
                return 0.0
        
        # Extract PKT codes
        IKTBV = get_time_value('IKTBV')
        IKTHD = get_time_value('IKTHD')
        IKMBV = get_time_value('IKMBV')
        IKMHD = get_time_value('IKMHD')
        
        # Extract other codes (9 codes total)
        other_codes = ['ITNBM', 'ITTBS', 'IVNBM', 'IVTBS', 'IRNBM', 'IRNXS', 'IRLSP', 'IDLSS', 'IDDGS']
        total_other_time = sum(get_time_value(code) for code in other_codes)
        
        # Extract IXXLT and IXXLM codes
        IXXLT = get_time_value('IXXLT')
        IXXLM = get_time_value('IXXLM')
        
        # Calculate PKT time based on sll conditions
        if sll <= 2:
            pkt_time = sll * IKTBV + sll * IKMBV
        elif sll <= 10:  # Changed: 2 < sll <= 10
            pkt_time = 2 * IKTBV + (sll - 2) * IKTHD + IKMBV + (sll - 2) * IKMHD
        else:  # sll > 10 (Changed from >= 10)
            pkt_time = 1 * IKTBV + (sll - 1) * IKTHD + IKMBV + (sll - 1) * IKMHD
        
        # Calculate other groups time
        # Formula: (ITNBM + ITTBS + IVNBM + IVTBS + IRNBM + IRNXS + IRLSP + IDLSS + IDDGS) × sll
        other_time = total_other_time * sll
        
        # Calculate IXXLT and IXXLM time
        # Formula: (sll × IXXLT) + (sll × IXXLM)
        ixlt_ixlm_time = sll * IXXLT + sll * IXXLM
        
        # Total time = PKT time + Other time + IXXLT/IXXLM time
        time = pkt_time + other_time + ixlt_ixlm_time
        total_completion_time += time
    
    # ============= Calculate CS Tổng =============
    if tong_thoi_gian_nang_luc_du_kien > 0:
        cs_tong = (total_completion_time / tong_thoi_gian_nang_luc_du_kien) * 100
    else:
        cs_tong = 0
    
    # ============= Calculate CS Trực Tiếp =============
    # Use tong_sl_nsu_tructiep_lam_12h (direct 12h workers only)
    cs_truc_tiep = 0
    thoi_gian_nguoi_truc_tiep = 0
    
    if len(df_hr_filtered) > 0:
        # Calculate direct worker time
        # = (Practical Employees - tong_sl_nsu_tructiep_lam_12h) × 6.5 × 60 + tong_sl_nsu_tructiep_lam_12h × 10 × 60
        thoi_gian_nguoi_truc_tiep = (tong_sl_nsu_tructiep_lam_8h) * 6.5 * 60 + tong_sl_nsu_tructiep_lam_12h * 10 * 60
        
        # Calculate CS trực tiếp
        if thoi_gian_nguoi_truc_tiep > 0:
            cs_truc_tiep = (total_completion_time / thoi_gian_nguoi_truc_tiep) * 100
    
    result = {
        'cs_tong': cs_tong,
        'cs_truc_tiep': cs_truc_tiep,
        'A_tong': tong_sl_nsu_dangky_lam_12h,
        'A_truc_tiep': tong_sl_nsu_tructiep_lam_12h,
        'B_tong': tong_sl_nsu_dangky_lam_8h,
        'practical_employees_count': tong_sl_nsu_tructiep_lam_8h + tong_sl_nsu_tructiep_lam_12h,
        'thoi_gian_100_nguoi': tong_thoi_gian_nang_luc_du_kien,
        'thoi_gian_nguoi_truc_tiep': thoi_gian_nguoi_truc_tiep,
        'total_completion_time': total_completion_time
    }
    
    return result
