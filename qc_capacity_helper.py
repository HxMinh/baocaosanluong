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
        'A': 0,
        'B': 0,
        'thoi_gian_100_nguoi': 0,
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
    
    # ============= Calculate A (12h workers) =============
    # PRIORITY 1: Try to get from Daily Head Counts first
    A = 0
    df_hr_filtered = df_hr_daily_head_counts[
        (df_hr_daily_head_counts['Department ID'] == '0300_BPKT') &
        (df_hr_daily_head_counts['Working Date Parsed'] == test_date_parsed)
    ].copy()
    
    if len(df_hr_filtered) > 0:
        # Try to get from "Tong So Nguoi Lam Them Gio 12h Truc Tiep" column
        if 'Tong So Nguoi Lam Them Gio 12h Truc Tiep' in df_hr_filtered.columns:
            a_str = str(df_hr_filtered['Tong So Nguoi Lam Them Gio 12h Truc Tiep'].iloc[0]).strip()
            if a_str and a_str != '' and a_str != 'nan':
                try:
                    A = int(float(a_str.replace(',', '.')))
                except:
                    A = 0
    
    # PRIORITY 2: If A is still 0, fallback to Shift Schedule logic
    if A == 0:
        df_shift_filtered = df_shift_schedule[
            (df_shift_schedule['Department ID'] == '0300_BPKT') &
            (df_shift_schedule['Work Date Parsed'] == test_date_parsed)
        ].copy()
        
        d12_count = len(df_shift_filtered[df_shift_filtered['Shift Type ID'] == 'D12'])
        s12_count = len(df_shift_filtered[df_shift_filtered['Shift Type ID'] == 'S12'])
        A = d12_count + s12_count
    
    # ============= Calculate B (8h workers) =============
    # df_hr_filtered already loaded above
    
    if len(df_hr_filtered) > 0:
        dept_emp_count_str = df_hr_filtered['Department Employees Count'].iloc[0]
        dept_emp_count = float(str(dept_emp_count_str).replace(',', '.'))
        B = dept_emp_count - A
    else:
        B = 0
    
    # ============= Calculate 100-person time =============
    thoi_gian_100_nguoi = (A * 10 * 60) + (B * 6.5 * 60)
    
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
        
        IKTBV = get_time_value('IKTBV')
        IKTHD = get_time_value('IKTHD')
        IKMBV = get_time_value('IKMBV')
        IKMHD = get_time_value('IKMHD')
        
        # Extract other codes (9 codes total)
        other_codes = ['ITNBM', 'ITTBS', 'IVNBM', 'IVTBS', 'IRNBM', 'IRNXS', 'IRLSP', 'IDLSS', 'IDDGS']
        total_other_time = sum(get_time_value(code) for code in other_codes)
        
        # Calculate PKT time based on sll conditions
        if sll <= 2:
            pkt_time = sll * IKTBV + sll * IKMBV
        elif sll < 10:
            pkt_time = 2 * IKTBV + (sll - 2) * IKTHD + IKMBV + (sll - 2) * IKMHD
        else:  # sll >= 10
            pkt_time = 1 * IKTBV + (sll - 1) * IKTHD + IKMBV + (sll - 1) * IKMHD
        
        # Calculate other groups time
        other_time = total_other_time * sll
        
        # Total time = Other groups + PKT
        time = other_time + pkt_time
        total_completion_time += time
    
    # ============= Calculate CS Tổng =============
    if thoi_gian_100_nguoi > 0:
        cs_tong = (total_completion_time / thoi_gian_100_nguoi) * 100
    else:
        cs_tong = 0
    
    # ============= Calculate CS Trực Tiếp =============
    cs_truc_tiep = 0
    thoi_gian_nguoi_truc_tiep = 0
    practical_employees_count = 0
    
    if len(df_hr_filtered) > 0:
        # Get Practical Employees Count
        practical_emp_str = df_hr_filtered['Practical Employees Count'].iloc[0]
        practical_employees_count = float(str(practical_emp_str).replace(',', '.'))
        
        # Calculate direct worker time
        # = (Practical Employees - A) × 6.5 × 60 + A × 10 × 60
        thoi_gian_nguoi_truc_tiep = (practical_employees_count - A) * 6.5 * 60 + A * 10 * 60
        
        # Calculate CS trực tiếp
        if thoi_gian_nguoi_truc_tiep > 0:
            cs_truc_tiep = (total_completion_time / thoi_gian_nguoi_truc_tiep) * 100
    
    result = {
        'cs_tong': cs_tong,
        'cs_truc_tiep': cs_truc_tiep,
        'A': A,
        'B': B,
        'practical_employees_count': practical_employees_count,
        'thoi_gian_100_nguoi': thoi_gian_100_nguoi,
        'thoi_gian_nguoi_truc_tiep': thoi_gian_nguoi_truc_tiep,
        'total_completion_time': total_completion_time
    }
    
    return result
