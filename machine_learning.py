from sklearn.linear_model import LinearRegression

def calculate_contact_efficiency(percent_data):
    
    #バットスピードから期待される平均打球速度と実際の平均打球速度の差をcontact_efficiencyと定義し、それをパーセンタイル化する関数

    data = percent_data[["player_id","bat_speed","exit_velocity"]].dropna().copy()

    X = data[["bat_speed"]]
    y = data["exit_velocity"]

    model = LinearRegression()
    model.fit(X, y)

    data["predicted_exit_velocity"] = model.predict(X)
    data["contact_efficiency"] = (data["exit_velocity"]- data["predicted_exit_velocity"])
    data["contact_efficiency_percentile"] = (data["contact_efficiency"].rank(pct=True)* 100)

    return data[["player_id","contact_efficiency_percentile"]]

def calculate_weight(batter_percent_data,batter_exitvelo_data,batter_contact_efficiency_data):
    
    #ミートに用いた指標＋パワーに用いた指標とxwOBAという打者の総合力を表す指標との相関を分析し、
    #それぞれの指標がどの程度の影響力を持つかを計算する関数
    #計算した重さはミートを計算する際に使用するため、bat_speed（パワーの計算に使う指標）を除いた部分を辞書として返している。

    data =(
        batter_percent_data.copy()
        .merge(batter_exitvelo_data,on="player_id")
        .merge(batter_contact_efficiency_data,on="player_id")
    )
    
    data=data[[
        "player_id",
        "xwoba",
        "whiff_percent",
        "chase_percent",
        "squared_up_rate",
        "bat_speed",
        "anglesweetspotpercent",
        "contact_efficiency_percentile"
    ]].dropna()
    
    X = data[[
        "whiff_percent",
        "chase_percent",
        "squared_up_rate",
        "bat_speed",
        "anglesweetspotpercent",
        "contact_efficiency_percentile"
    ]]
    y = data["xwoba"]

    model = LinearRegression()
    model.fit(X, y)

    coefficients = dict(
        zip(
            X.columns,
            model.coef_
        )
    )
    
    return coefficients

def analyze_contact_efficiency(percent_data,contact_efficiency_data):
    data = percent_data.merge(contact_efficiency_data,on="player_id")
    data = data[["xwoba","squared_up_rate","contact_efficiency_percentile"]].dropna()
    contact_correlation= data["xwoba"].corr(data["contact_efficiency_percentile"])
    squared_correlation= data["xwoba"].corr(data["squared_up_rate"])
    
    print("Contact Efficiency:",contact_correlation)
    print("Squared-Up:",squared_correlation)