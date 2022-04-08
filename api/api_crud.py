import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from utils import do_sql_cmd, do_sql_sel
from func import cfg
from models import Item

api_crud_bp = Blueprint(
    "api_crud_bp",
    __name__,
)


dict_phones = cfg.get("dict_phones")


@api_crud_bp.route("/api/costs", methods=["POST"])
@cross_origin()
@jwt_required()
def new_cost():
    """
    insert a new cost
    input: rdate,cat,sub_cat,mydesc,suma
    """
    req = request.get_json()
    res = do_sql_cmd(
        f"""insert into `myBudj` (rdate,cat,sub_cat,mydesc,suma) 
        values ('{req.get("rdate","")}', '{req['cat']}', '{req.get("sub_cat","")}','{req.get("mydesc","")}',{req['suma']})"""
    )
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"], "id": res["rowcount"]})


@api_crud_bp.route("/api/costs/", methods=["GET"])
# @cross_origin(supports_credentials=True)
@cross_origin()
@jwt_required()
def ret_costs():
    """
    list or search all costs.
    if not set conditions year and month then get current year and month
    if set q then do search
    input: q,cat,year,month
    """
    q = request.args.get("q", "")
    sort = request.args.get("sort", "")
    cat = request.args.get("cat", "")
    year = request.args.get("year", "")
    month = request.args.get("month", "")
    # print(f"sort: {sort}, year: {year}, month: {month}")

    um = []

    if q:
        um.append(
            f" and (`cat` like '%{q}%' or  `sub_cat` like '%{q}%' or  `mydesc` like '%{q}%' or `owner` like '%{q}%')"
        )

    if not sort:
        sort = "order by suma desc"
    elif sort == "1":
        sort = "order by rdate desc"
    elif sort == "2":
        sort = "order by cat"
    elif sort == "3":
        sort = "order by suma desc"
    else:
        sort = "order by  suma desc"

    if year:
        um.append(f" and extract(YEAR from rdate)={year}")
    else:
        um.append(f" and extract(YEAR from rdate)=extract(YEAR from now())")
    if month:
        um.append(f" and extract(MONTH from rdate)={month}")
    else:
        um.append(f" and extract(MONTH from rdate)=extract(MONTH from now())")

    if cat and cat != "last":
        um.append(f" and cat='{cat}'")
    else:
        um = []
        um.append(f" and rdate>=DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY) ")

    sql = f"""
select id,rdate,cat,sub_cat,mydesc,suma
from `myBudj`
where 1=1 {' '.join(um)}
{sort}
"""
    # print(sql)
    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    phone_number = ""
    res = [dict(row) for row in do_sql_sel(sql)]
    if res[0].get("rowcount") is not None and res[0].get("rowcount") < 0:
        return jsonify([{"cat": "Помилки", "mydesc": "Помилка виконання запиту"}])
    for r in res:
        if pattern.search(r["sub_cat"]):
            phone_number = pattern.search(r["sub_cat"]).group(0)
            if phone_number in dict_phones:
                r["mydesc"] += dict_phones[phone_number]

    return jsonify(res)


@api_crud_bp.route("/api/costs/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def ret_cost(id):
    """
    get info about cost
    input: id
    """
    sql = f"select id,rdate,cat,sub_cat,mydesc,suma from myBudj where id={id}"
    res = do_sql_sel(sql)
    # for r in res:
    # print(f"{r=}")
    # return jsonify([dict(row) for row in do_sql_sel(sql)])
    return jsonify([dict(row) for row in res])


@api_crud_bp.route("/api/costs/<int:id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def del_cost(id):
    """
    mark delete cost
    input: id
    """
    res = do_sql_cmd(f"update myBudj set deleted=1 where id={id}")
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"]})


@api_crud_bp.route("/api/costs/<id>", methods=["PUT"])
@cross_origin()
@jwt_required()
def upd_cost(id):
    """
    update a cost
    input: rdate,cat,sub_cat,mydesc,suma,id
    """
    req = request.get_json()
    sql = f"""update myBudj set cat='{req['cat']}', rdate='{req['rdate']}', sub_cat='{req.get("sub_cat","")}',mydesc='{req.get("mydesc","")}'
        ,suma={req['suma']}  
        where id={id}"""
    # print(sql)
    res = do_sql_cmd(sql)
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"]})
