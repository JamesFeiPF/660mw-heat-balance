"""MHFlow 水蒸汽物性模块

基于 IAPWS-IF97 标准计算水和水蒸气的热物性参数。
优先使用 iapws 库，若不可用则使用内置的简化公式实现。
"""
import math
import warnings

# 尝试导入 iapws 库
try:
    from iapws import IAPWS97
    IAPWS_AVAILABLE = True
except ImportError:
    IAPWS_AVAILABLE = False
    warnings.warn(
        "iapws 库不可用，将使用内置的 IAPWS-IF97 简化公式。"
        "建议安装: pip install iapws",
        UserWarning,
        stacklevel=2,
    )


# ============================================================
# IAPWS-IF97 简化公式 (fallback)
# ============================================================

# 区域边界常数
_P_CRIT = 22.064  # 临界压力 MPa
_T_CRIT = 647.096  # 临界温度 K
_P_TRIPLE = 0.000611657  # 三相点压力 MPa
_T_TRIPLE = 273.16  # 三相点温度 K


def _saturation_pressure_iapws97(t_c: float) -> float:
    """
    IAPWS-IF97 饱和压力公式 (区域4)
    t_c: 温度 (°C)
    返回: 饱和压力 (MPa)
    """
    t = t_c + 273.15  # 转换为K
    beta = 1.0 - t / _T_CRIT
    # 简化 Wagner 公式系数
    n = [
        0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2,
        0.12020824702470e5, -0.32325550322333e7, 0.14915108613530e2,
        -0.48232657361591e4, 0.40511340542057e6, -0.23855557567849,
        0.65017534844798e3,
    ]
    a = beta**2 + n[2] * beta + n[5]
    b = n[0] * beta**2 + n[3] * beta + n[6]
    c = n[1] * beta**2 + n[4] * beta + n[7]
    d = n[8] * beta**2 + n[9] * beta
    p = (2.0 * c / (-b - math.sqrt(b**2 - 4.0 * a * c))) * 1.0e-3  # MPa
    return p


def _saturation_temperature_iapws97(p_mpa: float) -> float:
    """
    IAPWS-IF97 饱和温度公式 (区域4)
    p_mpa: 压力 (MPa)
    返回: 饱和温度 (°C)
    """
    p = p_mpa  # MPa
    beta = math.sqrt(p / 1.0)  # 简化
    # 使用迭代法求饱和温度
    t_guess = 100.0  # 初始猜测
    for _ in range(50):
        p_calc = _saturation_pressure_iapws97(t_guess)
        # 牛顿法
        dt = 0.01
        dp_dt = (_saturation_pressure_iapws97(t_guess + dt) - p_calc) / dt
        if abs(dp_dt) < 1e-12:
            break
        t_guess = t_guess - (p_calc - p) / dp_dt
        if t_guess < 1.0:
            t_guess = 1.0
        if t_guess > 370.0:
            t_guess = 370.0
    return t_guess


def _specific_enthalpy_water_iapws97(p_mpa: float, t_c: float) -> float:
    """
    IAPWS-IF97 区域1 (亚冷水) 简化比焓公式
    p_mpa: 压力 (MPa)
    t_c: 温度 (°C)
    返回: 比焓 (kJ/kg)
    """
    # 简化公式: h ≈ cp * T (对于液态水, cp ≈ 4.18 kJ/(kg·K))
    # 更精确的简化:
    t = t_c + 273.15
    p = p_mpa

    # 参考态: 0.01°C 饱和水 h = 0 kJ/kg (近似)
    # 使用简化多项式
    tau = 1386.0 / t
    pi = p / 16.529

    # 理想气体部分 (简化)
    g0 = -7.83952 * tau + 1.0 / tau * (
        0.5 * math.log(tau) - 2.9219 * tau**(-1) + 1.6398 * tau**(-2)
        - 0.5 * math.log(pi)
    )

    # 残余部分 (简化)
    gr = (
        0.02814 * pi * tau**(-1) + 0.00127 * pi * tau**(-2)
        - 0.00042 * pi**2 * tau**(-1)
    )

    # h = g + T*s, 简化计算
    h = t * (g0 + gr) * 0.001  # 简化缩放

    # 使用更直接的简化方法
    # 对于液态水, h ≈ 4.186 * T(°C) + 压力修正
    h = 4.186 * t_c + 0.1 * p_mpa * 0.1

    # 饱和水焓值表插值修正 (关键点)
    sat_data = [
        (0.01, 0.0), (50, 209.3), (100, 419.0), (150, 632.2),
        (200, 852.4), (250, 1085.3), (300, 1344.0),
    ]
    if t_c <= 300 and p_mpa <= _saturation_pressure_iapws97(t_c) + 0.1:
        # 亚冷或饱和水, 用表插值
        for i in range(len(sat_data) - 1):
            if sat_data[i][0] <= t_c <= sat_data[i + 1][0]:
                t1, h1 = sat_data[i]
                t2, h2 = sat_data[i + 1]
                frac = (t_c - t1) / (t2 - t1)
                h = h1 + frac * (h2 - h1)
                # 压力修正 (简化)
                p_sat = _saturation_pressure_iapws97(t_c)
                if p_mpa > p_sat:
                    h += 0.001 * (p_mpa - p_sat) * 1000
                break

    return h


def _specific_enthalpy_steam_iapws97(p_mpa: float, t_c: float) -> float:
    """
    IAPWS-IF97 区域2 (过热蒸汽) 简化比焓公式
    p_mpa: 压力 (MPa)
    t_c: 温度 (°C)
    返回: 比焓 (kJ/kg)
    """
    # 过热蒸汽焓的简化计算
    # h = h_sat + cp_steam * (T - T_sat)
    t_sat = _saturation_temperature_iapws97(p_mpa)

    # 饱和蒸汽焓 (简化表)
    sat_h_data = [
        (0.001, 2501.0), (0.01, 2584.0), (0.1, 2675.0),
        (1.0, 2778.0), (5.0, 2794.0), (10.0, 2725.0),
        (15.0, 2611.0), (20.0, 2293.0),
    ]
    h_sat = 2675.0  # 默认值
    for i in range(len(sat_h_data) - 1):
        if sat_h_data[i][0] <= p_mpa <= sat_h_data[i + 1][0]:
            p1, h1 = sat_h_data[i]
            p2, h2 = sat_h_data[i + 1]
            frac = (p_mpa - p1) / (p2 - p1)
            h_sat = h1 + frac * (h2 - h1)
            break

    # 过热蒸汽平均比热 (随压力温度变化)
    # 简化: cp_steam ≈ 2.0 ~ 2.5 kJ/(kg·K) 对于中低压
    if p_mpa < 1.0:
        cp_steam = 2.0
    elif p_mpa < 10.0:
        cp_steam = 2.2
    else:
        cp_steam = 2.5

    # 温度修正: 高温时比热增大
    if t_c > 500:
        cp_steam += 0.3 * (t_c - 500) / 200.0

    h = h_sat + cp_steam * (t_c - t_sat)

    # 对于超临界区域 (p > 22.064 MPa)
    if p_mpa > _P_CRIT:
        # 超临界流体焓
        h = 4.186 * t_c + 1500.0 + 0.5 * (p_mpa - 22.0) * 50.0

    return h


def _specific_entropy_water_iapws97(p_mpa: float, t_c: float) -> float:
    """
    IAPWS-IF97 区域1 简化比熵公式
    返回: 比熵 (kJ/(kg·K))
    """
    # 简化: s ≈ cp * ln(T/T_ref) 对于液态水
    t = t_c + 273.15
    s = 4.186 * math.log(t / 273.16)

    # 压力修正
    p_sat = _saturation_pressure_iapws97(t_c)
    if p_mpa > p_sat and p_mpa > 0.01:
        s -= 0.001 * (p_mpa - p_sat) * 0.1

    return s


def _specific_entropy_steam_iapws97(p_mpa: float, t_c: float) -> float:
    """
    IAPWS-IF97 区域2 简化比熵公式
    返回: 比熵 (kJ/(kg·K))
    """
    t_sat = _saturation_temperature_iapws97(p_mpa)
    t = t_c + 273.15
    t_sat_k = t_sat + 273.15

    # 饱和蒸汽熵 (简化)
    sat_s_data = [
        (0.001, 9.156), (0.01, 8.901), (0.1, 7.359),
        (1.0, 6.587), (5.0, 5.973), (10.0, 5.614),
        (15.0, 5.312), (20.0, 4.934),
    ]
    s_sat = 7.359
    for i in range(len(sat_s_data) - 1):
        if sat_s_data[i][0] <= p_mpa <= sat_s_data[i + 1][0]:
            p1, s1 = sat_s_data[i]
            p2, s2 = sat_s_data[i + 1]
            frac = (p_mpa - p1) / (p2 - p1)
            s_sat = s1 + frac * (s2 - s1)
            break

    # 过热蒸汽熵增量
    if p_mpa < 1.0:
        cp_steam = 2.0
    elif p_mpa < 10.0:
        cp_steam = 2.2
    else:
        cp_steam = 2.5

    if t_c > 500:
        cp_steam += 0.3 * (t_c - 500) / 200.0

    s = s_sat + cp_steam * math.log(t / t_sat_k)

    return s


def _ph_to_t_fallback(p_mpa: float, h_kjkg: float) -> float:
    """
    由压力和比焓求温度 (简化)
    p_mpa: 压力 (MPa)
    h_kjkg: 比焓 (kJ/kg)
    返回: 温度 (°C)
    """
    # 饱和参数
    try:
        t_sat = _saturation_temperature_iapws97(p_mpa)
    except Exception:
        t_sat = 100.0

    # 饱和水焓和饱和蒸汽焓
    h_f = _specific_enthalpy_water_iapws97(p_mpa, t_sat)
    h_g = _specific_enthalpy_steam_iapws97(p_mpa, t_sat)

    if h_kjkg <= h_f:
        # 亚冷水
        # h ≈ cp * T => T ≈ h / cp
        t = h_kjkg / 4.186
        return t
    elif h_kjkg >= h_g:
        # 过热蒸汽
        # h = h_g + cp * (T - T_sat)
        if p_mpa < 1.0:
            cp_steam = 2.0
        elif p_mpa < 10.0:
            cp_steam = 2.2
        else:
            cp_steam = 2.5
        t = t_sat + (h_kjkg - h_g) / cp_steam
        return t
    else:
        # 两相区
        return t_sat


def _ph_to_s_fallback(p_mpa: float, h_kjkg: float) -> float:
    """
    由压力和比焓求比熵 (简化)
    """
    t = _ph_to_t_fallback(p_mpa, h_kjkg)
    return ps_to_s(p_mpa, t)


def _ps_to_t_fallback(p_mpa: float, s_kjkgk: float) -> float:
    """
    由压力和比熵求温度 (简化)
    """
    try:
        t_sat = _saturation_temperature_iapws97(p_mpa)
    except Exception:
        t_sat = 100.0

    # 饱和水熵和饱和蒸汽熵
    s_f = _specific_entropy_water_iapws97(p_mpa, t_sat)
    s_g = _specific_entropy_steam_iapws97(p_mpa, t_sat)

    if s_kjkgk <= s_f:
        # 亚冷水
        t = 273.16 * math.exp(s_kjkgk / 4.186)
        return t
    elif s_kjkgk >= s_g:
        # 过热蒸汽
        t_sat_k = t_sat + 273.15
        if p_mpa < 1.0:
            cp_steam = 2.0
        elif p_mpa < 10.0:
            cp_steam = 2.2
        else:
            cp_steam = 2.5
        t = t_sat_k * math.exp((s_kjkgk - s_g) / cp_steam) - 273.15
        return t
    else:
        # 两相区
        return t_sat


def ps_to_s(p_mpa: float, t_c: float) -> float:
    """
    由压力和温度求比熵 (统一接口)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p_mpa, T=t_c + 273.15)
            return sub.s
        except Exception:
            pass
    # fallback
    if t_c < _saturation_temperature_iapws97(p_mpa) or p_mpa > _P_CRIT:
        return _specific_entropy_water_iapws97(p_mpa, t_c)
    else:
        return _specific_entropy_steam_iapws97(p_mpa, t_c)


# ============================================================
# 统一接口函数
# ============================================================

def pt_to_h(p: float, t: float) -> float:
    """
    由压力和温度求比焓

    参数:
        p: 压力 (MPa)
        t: 温度 (°C)

    返回:
        比焓 (kJ/kg)
    """
    if IAPWS_AVAILABLE:
        try:
            t_sat = saturation_temperature(p)
            sub = IAPWS97(P=p, T=t + 273.15)
            # iapws在饱和边界返回蒸汽相，需要检查
            # 如果Liquid.h不为None，说明是液态
            if sub.Liquid.h is not None:
                return sub.h
            elif t <= t_sat:
                # 在饱和线上或亚冷区，但iapws返回了蒸汽相
                # 使用饱和水焓 + 温度修正
                sub_f = IAPWS97(P=p, x=0)
                if t < t_sat:
                    return sub_f.h + 4.186 * (t - t_sat)
                else:
                    return sub_f.h
            else:
                return sub.h
        except Exception:
            pass

    # fallback: 简化公式
    if p > _P_CRIT:
        # 超临界区域
        return _specific_enthalpy_steam_iapws97(p, t)

    try:
        t_sat = _saturation_temperature_iapws97(p)
    except Exception:
        t_sat = 100.0

    if t < t_sat:
        return _specific_enthalpy_water_iapws97(p, t)
    else:
        return _specific_enthalpy_steam_iapws97(p, t)


def pt_to_s(p: float, t: float) -> float:
    """
    由压力和温度求比熵

    参数:
        p: 压力 (MPa)
        t: 温度 (°C)

    返回:
        比熵 (kJ/(kg·K))
    """
    if IAPWS_AVAILABLE:
        try:
            t_sat = saturation_temperature(p)
            sub = IAPWS97(P=p, T=t + 273.15)
            if sub.Liquid.h is not None:
                return sub.s
            elif t <= t_sat:
                sub_f = IAPWS97(P=p, x=0)
                if t < t_sat:
                    return sub_f.s + 4.186 * math.log((t + 273.15) / (t_sat + 273.15))
                else:
                    return sub_f.s
            else:
                return sub.s
        except Exception:
            pass

    # fallback
    if p > _P_CRIT:
        return _specific_entropy_steam_iapws97(p, t)

    try:
        t_sat = _saturation_temperature_iapws97(p)
    except Exception:
        t_sat = 100.0

    if t < t_sat:
        return _specific_entropy_water_iapws97(p, t)
    else:
        return _specific_entropy_steam_iapws97(p, t)


def ph_to_t(p: float, h: float) -> float:
    """
    由压力和比焓求温度

    参数:
        p: 压力 (MPa)
        h: 比焓 (kJ/kg)

    返回:
        温度 (°C)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, h=h)
            return sub.T - 273.15
        except Exception:
            pass

    # fallback
    return _ph_to_t_fallback(p, h)


def ph_to_s(p: float, h: float) -> float:
    """
    由压力和比焓求比熵

    参数:
        p: 压力 (MPa)
        h: 比焓 (kJ/kg)

    返回:
        比熵 (kJ/(kg·K))
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, h=h)
            return sub.s
        except Exception:
            pass

    # fallback
    return _ph_to_s_fallback(p, h)


def ps_to_t(p: float, s: float) -> float:
    """
    由压力和比熵求温度

    参数:
        p: 压力 (MPa)
        s: 比熵 (kJ/(kg·K))

    返回:
        温度 (°C)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, s=s)
            return sub.T - 273.15
        except Exception:
            pass

    # fallback
    return _ps_to_t_fallback(p, s)


def px_to_h(p: float, x: float) -> float:
    """
    由压力和干度求比焓

    参数:
        p: 压力 (MPa)
        x: 干度 (0~1)

    返回:
        比焓 (kJ/kg)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, x=x)
            return sub.h
        except Exception:
            pass

    # fallback
    t_sat = _saturation_temperature_iapws97(p)
    h_f = _specific_enthalpy_water_iapws97(p, t_sat)
    h_g = _specific_enthalpy_steam_iapws97(p, t_sat)
    return h_f + x * (h_g - h_f)


def px_to_s(p: float, x: float) -> float:
    """
    由压力和干度求比熵

    参数:
        p: 压力 (MPa)
        x: 干度 (0~1)

    返回:
        比熵 (kJ/(kg·K))
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, x=x)
            return sub.s
        except Exception:
            pass

    # fallback
    t_sat = _saturation_temperature_iapws97(p)
    s_f = _specific_entropy_water_iapws97(p, t_sat)
    s_g = _specific_entropy_steam_iapws97(p, t_sat)
    return s_f + x * (s_g - s_f)


def px_to_t(p: float, x: float) -> float:
    """
    由压力和干度求温度

    参数:
        p: 压力 (MPa)
        x: 干度 (0~1)

    返回:
        温度 (°C)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, x=x)
            return sub.T - 273.15
        except Exception:
            pass

    # fallback
    return _saturation_temperature_iapws97(p)


def saturation_temperature(p: float) -> float:
    """
    由压力求饱和温度

    参数:
        p: 压力 (MPa)

    返回:
        饱和温度 (°C)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, x=0)
            return sub.T - 273.15
        except Exception:
            pass

    return _saturation_temperature_iapws97(p)


def saturation_pressure(t: float) -> float:
    """
    由温度求饱和压力

    参数:
        t: 温度 (°C)

    返回:
        饱和压力 (MPa)
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(T=t + 273.15, x=0)
            return sub.P
        except Exception:
            pass

    return _saturation_pressure_iapws97(t)


def saturation_properties(p: float) -> dict:
    """
    由压力求饱和水和饱和蒸汽参数

    参数:
        p: 压力 (MPa)

    返回:
        dict: {
            't_sat': 饱和温度(°C),
            'h_f': 饱和水比焓(kJ/kg),
            'h_g': 饱和蒸汽比焓(kJ/kg),
            's_f': 饱和水比熵(kJ/(kg·K)),
            's_g': 饱和蒸汽比熵(kJ/(kg·K)),
            'v_f': 饱和水比容(m³/kg),
            'v_g': 饱和蒸汽比容(m³/kg),
        }
    """
    t_sat = saturation_temperature(p)

    if IAPWS_AVAILABLE:
        try:
            sub_f = IAPWS97(P=p, x=0)
            sub_g = IAPWS97(P=p, x=1)
            return {
                't_sat': t_sat,
                'h_f': sub_f.h,
                'h_g': sub_g.h,
                's_f': sub_f.s,
                's_g': sub_g.s,
                'v_f': sub_f.v,
                'v_g': sub_g.v,
            }
        except Exception:
            pass

    # fallback
    h_f = _specific_enthalpy_water_iapws97(p, t_sat)
    h_g = _specific_enthalpy_steam_iapws97(p, t_sat)
    s_f = _specific_entropy_water_iapws97(p, t_sat)
    s_g = _specific_entropy_steam_iapws97(p, t_sat)

    # 简化比容
    v_f = 0.001  # m³/kg (液态水近似)
    # 饱和蒸汽比容用理想气体近似
    v_g = 0.4615 * (t_sat + 273.15) / (p * 1000) if p > 0.001 else 100.0

    return {
        't_sat': t_sat,
        'h_f': h_f,
        'h_g': h_g,
        's_f': s_f,
        's_g': s_g,
        'v_f': v_f,
        'v_g': v_g,
    }


def get_steam_properties(p: float, t: float) -> dict:
    """
    获取指定压力温度下的完整水/水蒸气物性参数

    参数:
        p: 压力 (MPa)
        t: 温度 (°C)

    返回:
        dict: 包含 h, s, v, rho 等参数
    """
    if IAPWS_AVAILABLE:
        try:
            sub = IAPWS97(P=p, T=t + 273.15)
            return {
                'p': p,
                't': t,
                'h': sub.h,
                's': sub.s,
                'v': sub.v,
                'rho': 1.0 / sub.v if sub.v > 0 else 0,
                'cp': sub.cp,
                'phase': 'liquid' if sub.Liquid else ('gas' if sub.Vapor else 'two-phase'),
            }
        except Exception:
            pass

    # fallback
    h = pt_to_h(p, t)
    s = pt_to_s(p, t)
    return {
        'p': p,
        't': t,
        'h': h,
        's': s,
        'v': 0.001 if t < saturation_temperature(p) else 0.4615 * (t + 273.15) / (p * 1000 + 1e-10),
        'rho': 1000.0 if t < saturation_temperature(p) else p * 1000 / (0.4615 * (t + 273.15) + 1e-10),
        'cp': 4.186 if t < saturation_temperature(p) else 2.1,
        'phase': 'liquid' if t < saturation_temperature(p) else 'gas',
    }
