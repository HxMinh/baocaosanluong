# -*- coding: utf-8 -*-
"""
Helper functions for Quality Control Capacity Calculation
"""

import pandas as pd


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
    # A_tong: Total 12h workers (for CS Tổng)
    # A_truc_tiep: Direct 12h workers only (for CS Trực Tiếp)
    
    A_tong = 0
    A_truc_tiep = 0
    
    df_hr_filtered = df_hr_daily_head_counts[
        (df_hr_daily_head_counts['Department ID'] == '0300_BPKT') &
        (df_hr_daily_head_counts['Working Date Parsed'] == test_date_parsed)
    ].copy()
    
    if len(df_hr_filtered) > 0:
        # Get A_tong from "Tong So Nguoi Lam Them Gio 12h" (total 12h workers)
        if 'Tong So Nguoi Lam Them Gio 12h' in df_hr_filtered.columns:
            a_tong_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 12h'].iloc[0]).strip()
            if a_tong_str and a_tong_str != '' and a_tong_str != 'nan':
                try:
                    A_tong = int(float(a_tong_str.replace(',', '.')))
                except:
                    A_tong = 0
        
        # Get A_truc_tiep from "Tong So Nguoi Lam Them Gio 12h Truc Tiep" (direct 12h workers)
        if 'Tong So Nguoi Lam Them Gio 12h Truc Tiep' in df_hr_filtered.columns:
            a_truc_tiep_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 12h Truc Tiep'].iloc[0]).strip()
            if a_truc_tiep_str and a_truc_tiep_str != '' and a_truc_tiep_str != 'nan':
                try:
                    A_truc_tiep = int(float(a_truc_tiep_str.replace(',', '.')))
                except:
                    A_truc_tiep = 0
    
    # FALLBACK: If A_tong is still 0, use Shift Schedule
    if A_tong == 0:
        df_shift_filtered = df_shift_schedule[
            (df_shift_schedule['Department ID'] == '0300_BPKT') &
            (df_shift_schedule['Work Date Parsed'] == test_date_parsed)
        ].copy()
        
        d12_count = len(df_shift_filtered[df_shift_filtered['Shift Type ID'] == 'D12'])
        s12_count = len(df_shift_filtered[df_shift_filtered['Shift Type ID'] == 'S12'])
        A_tong = d12_count + s12_count
    
    # If A_truc_tiep is still 0, use A_tong as fallback
    if A_truc_tiep == 0:
        A_truc_tiep = A_tong
    
    # ============= Calculate B (8h workers) for CS Tổng =============
    # Use A_tong for calculating total workforce
    
    if len(df_hr_filtered) > 0:
        dept_emp_count_str = df_hr_filtered['Department Employees Count'].iloc[0]
        dept_emp_count = float(str(dept_emp_count_str).replace(',', '.'))
        B_tong = dept_emp_count - A_tong
    else:
        B_tong = 0
    
    # ============= Calculate 100-person time (for CS Tổng) =============
    thoi_gian_100_nguoi = (A_tong * 10 * 60) + (B_tong * 6.5 * 60)
    
    # ============= Calculate total completion time =============
    total_completion_time = 0
    
    for _, row in df_giao_kho_filtered.iterrows():
        ten_chi_tiet = row['ten_chi_tiet']
        sll_str = str(row['sll']).replace(',', '.')
        
        try:
            sll = float(sll_str)
        except:
            continue
        
        # Find matching time data
        df_time_match = df_thoi_gian_hoan_thanh[
            df_thoi_gian_hoan_thanh['ten_chi_tiet'] == ten_chi_tiet
        ].copy()
        
        if len(df_time_match) == 0:
            continue
        
        # Extract PKT codes
        def get_time_value(code):
            try:
                val = df_time_match[df_time_match['ma_cv'] == code]['Thoi_Gian'].iloc[0]
                return float(str(val).replace(',', '.'))
            except:
                return 0
        
        # Extract PKT codes
        IKTBV = get_time_value('IKTBV')
        IKTHD = get_time_value('IKTHD')
        IKMBV = get_time_value('IKMBV')
        IKMHD = get_time_value('IKMHD')
        
        # Extract other codes (9 codes total)
        other_codes = ['ITNBM', 'ITTBS', 'IVNBM', 'IVTBS', 'IRNBM', 'IRNXS', 'IRLSP', 'IDLSS', 'IDDGS']
        total_other_time = sum(get_time_value(code) for code in other_codes)
        
        # Extract IXLT and IXLM codes (NEW)
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
    if thoi_gian_100_nguoi > 0:
        cs_tong = (total_completion_time / thoi_gian_100_nguoi) * 100
    else:
        cs_tong = 0
    
    # ============= Calculate CS Trực Tiếp =============
    # Use A_truc_tiep (direct 12h workers only)
    cs_truc_tiep = 0
    thoi_gian_nguoi_truc_tiep = 0
    practical_employees_count = 0
    
    if len(df_hr_filtered) > 0:
        # Get Practical Employees Count
        practical_emp_str = df_hr_filtered['Practical Employees Count'].iloc[0]
        practical_employees_count = float(str(practical_emp_str).replace(',', '.'))
        
        # Calculate direct worker time
        # = (Practical Employees - A_truc_tiep) × 6.5 × 60 + A_truc_tiep × 10 × 60
        thoi_gian_nguoi_truc_tiep = (practical_employees_count - A_truc_tiep) * 6.5 * 60 + A_truc_tiep * 10 * 60
        
        # Calculate CS trực tiếp
        if thoi_gian_nguoi_truc_tiep > 0:
            cs_truc_tiep = (total_completion_time / thoi_gian_nguoi_truc_tiep) * 100
    
    result = {
        'cs_tong': cs_tong,
        'cs_truc_tiep': cs_truc_tiep,
        'A_tong': A_tong,
        'A_truc_tiep': A_truc_tiep,
        'B_tong': B_tong,
        'practical_employees_count': practical_employees_count,
        'thoi_gian_100_nguoi': thoi_gian_100_nguoi,
        'thoi_gian_nguoi_truc_tiep': thoi_gian_nguoi_truc_tiep,
        'total_completion_time': total_completion_time
    }
    
    return result
