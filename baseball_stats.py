from pybaseball import statcast_batter_percentile_ranks

def get_all_batters_data(year):
    
    #すべてのバッターのデータを出力する関数。htmlですべてのバッターから選択するプルダウンを表示する為に使用。
    
    return statcast_batter_percentile_ranks(year)[["player_name","player_id"]]

def data_to_percentile(data,index):
    
    #パーセンタイル化されていないデータをパーセンタイル化するために使用
    
    data[index]=data[index].rank(pct=True) * 100
    return data

def get_player_percentile(player_id, batter_percent_data, batter_exitvelo_data, batter_contact_efficiency_data):
    
    #引数として渡されたplayer_idに対応する指標を入手する為に使用
    
    player_percent_data = batter_percent_data[batter_percent_data["player_id"] == player_id]
    player_sweetspot_data = batter_exitvelo_data[batter_exitvelo_data["player_id"] == player_id]
    player_contact_efficiency_data = batter_contact_efficiency_data[batter_contact_efficiency_data["player_id"] == player_id]

    if player_percent_data.empty or player_sweetspot_data.empty or player_contact_efficiency_data.empty:
        return None, None ,None
    
    return player_percent_data, player_sweetspot_data ,player_contact_efficiency_data  

def meet_calculate(player_percentile_data,player_sweetspot_data,player_contact_efficiency_data,weight_dict):
    
    # ミートを計算するために使用。whiff(空振りする確率)、chase（ボール球を振る確率）、squared（バットの芯に当てる確率）、
    # contact_efficiency(独自指標。バットスピードから期待される打球速度と実際の打球速度の差)、sweet_spot（ボールをいい角度で打てる確率）からミートを計算。
    # 各種指標の重みはmachine_learning.pyの中で計算
    
    whiff = player_percentile_data["whiff_percent"].iloc[0]
    chase = player_percentile_data["chase_percent"].iloc[0]
    squared = player_percentile_data["squared_up_rate"].iloc[0]
    contact_efficiency =player_contact_efficiency_data["contact_efficiency_percentile"].iloc[0]
    sweet_spot = player_sweetspot_data["anglesweetspotpercent"].iloc[0]
    
    meet = 0
    weight=0

    if whiff == whiff:
        
        #whiffがNaN(欠落)していた場合NaN==NaNはFalseを返すため、欠落していた場合はその指標を無視している
        
        meet+=whiff*weight_dict["whiff_percent"]
        weight+=weight_dict["whiff_percent"]
    if chase == chase:
        meet+=chase*weight_dict["chase_percent"]
        weight+=weight_dict["chase_percent"]
    if  squared == squared:
        meet+=squared*weight_dict["squared_up_rate"]
        weight+=weight_dict["squared_up_rate"]
    if contact_efficiency == contact_efficiency:
        meet+=contact_efficiency*weight_dict["contact_efficiency_percentile"]
        weight+=weight_dict["contact_efficiency_percentile"]
    if sweet_spot == sweet_spot:
        meet+=sweet_spot*weight_dict["anglesweetspotpercent"]
        weight+=weight_dict["anglesweetspotpercent"]

    if  weight== 0:
        return None

    return round(meet/weight)

def power_calculate(player_percentile_data):
    power=player_percentile_data["bat_speed"].iloc[0]
    if power!=power:
        
        #大谷翔平選手など、打者として守備機会についていない場合は、指標が無い場合があるのでその場合は1を返すようにしている。
        
        power=1
    return round(power)

def speed_calculate(player_percentile_data):
    speed=player_percentile_data["sprint_speed"].iloc[0]
    if speed!=speed:
        speed=1
    return round(speed)

def arm_calculate(player_percentile_data):
    arm=player_percentile_data["arm_strength"].iloc[0]
    if arm!=arm:
        arm=1
        
    return round(arm)

def difence_calculate(player_percentile_data):
    difence=player_percentile_data["oaa"].iloc[0]
    if difence!=difence:
        difence=1
    return round(difence)