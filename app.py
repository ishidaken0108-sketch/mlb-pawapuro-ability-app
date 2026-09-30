from flask import Flask, render_template, request
from pybaseball import statcast_batter_percentile_ranks,statcast_batter_exitvelo_barrels

import baseball_stats
import machine_learning

# このプログラムの主目的:
#   MLBのデータ集積サイト baseballsavant上にある指標から、独自の新指標を提案し、その指標が打者の総合的な指標であるxwOBAにどの程度貢献するかを算出する。
#   baseballsavant上にはwhiff%（空振り率）chase%(ボール球を振る確率) squared-up %(打球を芯に当てる確率)など様々な指標が存在する。
#   しかし、イメージしやすいこれらの指標が低くても、打者としての総合的な優秀さを示すxwOBAが高くなっているなど、それぞれの指標がxwOBAに与える影響がわからなかった。
#   そのため、pythonの機械学習を用いてそれぞれの指標の重要度を計算する。
#   また、自分自身が考える新指標 「contact efficiency」が与える影響を考察する。
#
# contact efficiencyとは:
# 　bat-speed（バットを振る速さ）から統計的に期待される平均打球速度と実際打球速度の差異。
# 　バットスピードから期待される平均打球速度よりも実際の平均打球速度が高い場合、その打者はバットスピードを打球速度へ効率よく変換できていると考える。
# 　この能力は、ボールを強く正確に捉えるミート能力の一側面を表す可能性がある。
#
# 新指標を考えることとなった背景:
# 　バッターのミート（バットをボールに当てるうまさ）を考える際に有用な指標として、baseball-savant上にsquared-up %がある。
# 　Squared-Up%は、スイング速度と投球速度から物理的に可能な最大打球速度を求め、実際の打球速度がその80%以上に達した打球の割合を示す指標である。
#   つまり、芯に当てて安定して高い打球速度を出せていれば、この指標は高くなる。
# 　しかしながら、この指標を用いると常に80%程度の打球を打つバッターと100%の打球をたまに打つバッターでは、後者の評価が低くなってしまう。
#　 これは、アベレージヒッターとホームランバッターというスタイルの違いであり、打者としての優劣を示す際には不適切であると考える。
#  （パワプロ風に言えばミート多用と強振多用と言う違いでありパラメータの差ではない）
#　 そのため、新たな指標としてbat-speedから期待される平均打球速度と実際打球速度の違いであるcontact-effciencyを使用すれば
#　 アベレージヒッターとホームランバッターの両者を正しく評価できるのではないかと考えた。
#
# 分析の方法:
#   分析の一環としてMLBの各選手のデータから、実況パワフルプロ野球のようなパラメータを生成するサイトを作成する。
#   html,css,javascriptの勉強をする、楽しむ、分析をわかりやすくする事が目的である。
#
#   算出するパラメータは以下である。
#    ミート=バットをボールに当てるうまさ。　
#       対応するMLBの指標:whiff%（空振り率）chase%(ボール球を振る確率) 
#                       sweetspot%(打球をいい角度で打てる確率) squared-up %(打球を芯に当てる確率)
#                       contact_efficiency(このプログラム上で独自算出。batspeed(バットを振る速さ)から期待される平均打球速度と実際の平均打球速度のギャップ)
#
#    パワー=強い打球を生み出す能力。　
#       対応するMLBの指標:batspeed(バットを振る速さ)
#
#    走力=足の速さ。　
#       対応するMLBの指標:Sprint Speed(足の速さ)
#
#    肩力=投げるボールの速さ
#       対応するMLBの指標:Arm Strength(ボールの速さ)
#
#    守備力=守備のうまさ　
#       対応するMLBの指標:OAA(守備で平均と比較してどれくらい多くアウトを奪ったか)
#　
#　 なおパラメータ化に際しては、MLB平均を50として最小1　最大100　の相対評価として行う。


app = Flask(__name__)

# 公式ライブラリpybaseballを用いて、以下のデータを入手
#   batters(バッターの名前やid)
#   batter_percent_data(バッターの能力のパーセンタイル　パーセンタイル＝　1が最小 100が最大でその選手が下位から数えて何%に位置するかを表すもの　90の場合、上位10%であることを示す)
#   batter_exitvelo_data(打球速度のデータ。percent_dataにはないデータを使用する必要があるため別途入手し、それを関数を使用しパーセンタイル化している)
#   batter_contact_efficiency_data(バットスピードから期待される平均打球速度と実際の平均打球速度がミートの巧さであると解釈し、それをパーセンタイル化したデータ。)
        
year=2026
batters =baseball_stats.get_all_batters_data(year).sort_values("player_name")
batter_percent_data = statcast_batter_percentile_ranks(year)
batter_exitvelo_data = baseball_stats.data_to_percentile(statcast_batter_exitvelo_barrels(year),"anglesweetspotpercent")
batter_contact_efficiency_data = machine_learning.calculate_contact_efficiency(batter_percent_data)

# パワーや走力は対応する指標があるものの、ミートは空振り率、芯に当てる確率等を総合的にまとめたものであり、複数の指標から算出する必要がある。
# そのため、各種データのパーセンタイルを入手し、それらのデータがバッターのパワーを含めた総合的な打力を表す指標(xwOBA)へどの程度影響するかを算出する。
# その後、パワーを除いてミートに与える各種指標の重さを入手している

weight_dict=machine_learning.calculate_weight(batter_percent_data,batter_exitvelo_data,batter_contact_efficiency_data)

# contact_efficiencyとsquared-up %のどちらが優秀な指標かをxwOBAとの相関の強さにより分析する。

#machine_learning.analyze_contact_efficiency(batter_percent_data,batter_contact_efficiency_data)

# 実行した結果はContact Efficiencyが0.579、Squared-Upが0.047と、Contact Efficiencyの方がかなり相関が強い結果となった。
# どちらもバットスピードを基準として、統計的な打球速度を算出し、それを基準に測る点では同じなのにも関わらず大きな差が生じ、非常に興味深いと感じた。

@app.route("/", methods=["GET", "POST"])
def home():
    player_id,player_meet,player_power,player_speed,player_arm,player_difence,dataNone= (
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    )

    if request.method == "POST":

        player_id = int(request.form["player_id"])
        
        #htmlから受け取ったplayer_idに対応する各種指標の入手。
        
        player_percentile_data,player_sweetspot_data,player_contact_efficiency_data= baseball_stats.get_player_percentile(
            player_id,
            batter_percent_data,
            batter_exitvelo_data,
            batter_contact_efficiency_data
        )
        
        #player_idが存在しても、今年の出場数が足りない等でデータが存在していない可能性がある。その場合はdataNoneフラグをTrueにする。

        if player_percentile_data is None or player_sweetspot_data is None or player_contact_efficiency_data.empty:
            dataNone = True
        else:
            
        #各種データから算式に基づいて、ミート、パワー等に対応させる。ミートのみ複数の指標を使用する。
        
            player_meet,player_power,player_speed,player_arm,player_difence= (
                baseball_stats.meet_calculate(player_percentile_data,player_sweetspot_data,player_contact_efficiency_data,weight_dict),
                baseball_stats.power_calculate(player_percentile_data),
                baseball_stats.speed_calculate(player_percentile_data),
                baseball_stats.arm_calculate(player_percentile_data),
                baseball_stats.difence_calculate(player_percentile_data)
            )

    return render_template(
        "index.html",
        batters=batters,
        player_id=player_id,
        player_meet=player_meet,
        player_power=player_power,
        player_speed=player_speed,
        player_arm=player_arm,
        player_difence=player_difence,
        dataNone=dataNone
    )
    
#それぞれの指標から総合力を定義して、総合力順のランキングを表示するページを作成する。

@app.route("/rank")
def rank():
    ranking = []    
    
    sort = request.args.get("sort","overall")
    order = request.args.get("order","desc")

    for _, player in batters.iterrows():
        player_id = int(player["player_id"])
        player_name = (player["player_name"])
        player_percentile_data,player_sweetspot_data,player_contact_efficiency_data= baseball_stats.get_player_percentile(
            player_id,
            batter_percent_data,
            batter_exitvelo_data,
            batter_contact_efficiency_data
        )

        if (player_percentile_data is None or player_sweetspot_data is None or player_contact_efficiency_data.empty):
            continue

        meet = baseball_stats.meet_calculate(player_percentile_data,player_sweetspot_data,player_contact_efficiency_data,weight_dict)
        power = baseball_stats.power_calculate(player_percentile_data)
        speed = baseball_stats.speed_calculate(player_percentile_data)
        arm = baseball_stats.arm_calculate(player_percentile_data)
        difence = baseball_stats.difence_calculate(player_percentile_data)
        
        #少しミートとパワーが総合力に与える影響を大きく。

        fielding =(speed+ arm+ difence) / 3
        overall = round((meet+ power+ fielding)/3)

        ranking.append({
            "player_name": player_name,
            "overall": overall,
            "meet": meet,
            "power": power,
            "speed": speed,
            "arm": arm,
            "difence": difence
        })

    ranking = sorted(ranking,key=lambda player: player[sort],reverse=(order=="desc"))

    return render_template("rank.html",ranking=ranking,sort=sort,order=order)

if __name__ == "__main__":
    app.run(debug=True)