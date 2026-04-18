import json
import os
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from app import db
from app.models import Dataset, Transaction
from app.detector import detect_anomalies
from app.utils import (
    allowed_file,
    compute_stats,
    read_transaction_file,
    save_upload,
    validate_dataframe,
)

main = Blueprint("main", __name__)


@main.route("/")
def index():
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).limit(10).all()
    return render_template("index.html", datasets=datasets)


@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload CSV or Excel.", "danger")
            return redirect(request.url)

        filepath = save_upload(file, current_app.config["UPLOAD_FOLDER"])

        try:
            df = read_transaction_file(filepath)
        except Exception as e:
            flash(f"Error reading file: {e}", "danger")
            return redirect(request.url)

        valid, msg = validate_dataframe(df)
        if not valid:
            flash(f"Validation error: {msg}", "danger")
            return redirect(request.url)

        preview = df.head(20).to_dict(orient="records")
        columns = list(df.columns)

        return render_template(
            "upload.html",
            step="confirm",
            preview=preview,
            columns=columns,
            row_count=len(df),
            filepath=filepath,
        )

    return render_template("upload.html", step="upload")


@main.route("/analyze", methods=["POST"])
def analyze():
    filepath = request.form.get("filepath")
    method = request.form.get("method", "isolation_forest")
    threshold = float(request.form.get("threshold", 0.05))

    if not filepath or not os.path.exists(filepath):
        flash("File not found. Please upload again.", "danger")
        return redirect(url_for("main.upload"))

    df = read_transaction_file(filepath)
    df = detect_anomalies(df, method=method, contamination=threshold)

    dataset = Dataset(
        filename=os.path.basename(filepath),
        total_transactions=len(df),
        anomaly_count=int(df["is_anomaly"].sum()),
        detection_method=method,
        threshold=threshold,
    )
    db.session.add(dataset)
    db.session.flush()

    rows = []
    for _, row in df.iterrows():
        rows.append(
            Transaction(
                dataset_id=dataset.id,
                transaction_id=str(row["transaction_id"]),
                amount=float(row["amount"]),
                timestamp=pd.to_datetime(row["timestamp"]),
                merchant_category=str(row.get("merchant_category", "")),
                location=str(row.get("location", "")),
                user_id=str(row.get("user_id", "")),
                is_anomaly=bool(row["is_anomaly"]),
                anomaly_score=float(row["anomaly_score"]),
            )
        )
    db.session.bulk_save_objects(rows)
    db.session.commit()

    return redirect(url_for("main.dashboard", dataset_id=dataset.id))


@main.route("/dashboard/<int:dataset_id>")
def dashboard(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    txns = Transaction.query.filter_by(dataset_id=dataset_id).all()

    df = pd.DataFrame(
        [
            {
                "transaction_id": t.transaction_id,
                "amount": t.amount,
                "timestamp": t.timestamp,
                "merchant_category": t.merchant_category,
                "location": t.location,
                "user_id": t.user_id,
                "is_anomaly": t.is_anomaly,
                "anomaly_score": t.anomaly_score,
            }
            for t in txns
        ]
    )

    stats = compute_stats(df)

    # Chart 1: Time series with anomalies highlighted
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df_sorted = df.sort_values("timestamp")
    fig_ts = px.scatter(
        df_sorted,
        x="timestamp",
        y="amount",
        color="is_anomaly",
        color_discrete_map={True: "#e74c3c", False: "#3498db"},
        labels={"is_anomaly": "Anomaly", "amount": "Amount", "timestamp": "Time"},
        title="Transaction Timeline",
        hover_data=["transaction_id", "anomaly_score"],
    )
    fig_ts.update_layout(
        plot_bgcolor="#1e1e2f",
        paper_bgcolor="#1e1e2f",
        font_color="#e0e0e0",
        title_font_color="#ffffff",
    )
    chart_time = json.dumps(fig_ts, cls=plotly.utils.PlotlyJSONEncoder)

    # Chart 2: Amount distribution
    fig_dist = px.histogram(
        df,
        x="amount",
        color="is_anomaly",
        color_discrete_map={True: "#e74c3c", False: "#3498db"},
        nbins=50,
        title="Amount Distribution",
        labels={"amount": "Transaction Amount", "count": "Frequency"},
        barmode="overlay",
    )
    fig_dist.update_layout(
        plot_bgcolor="#1e1e2f",
        paper_bgcolor="#1e1e2f",
        font_color="#e0e0e0",
        title_font_color="#ffffff",
    )
    chart_dist = json.dumps(fig_dist, cls=plotly.utils.PlotlyJSONEncoder)

    # Chart 3: Anomaly score histogram
    fig_score = px.histogram(
        df,
        x="anomaly_score",
        nbins=50,
        title="Anomaly Score Distribution",
        labels={"anomaly_score": "Anomaly Score", "count": "Count"},
        color_discrete_sequence=["#9b59b6"],
    )
    fig_score.update_layout(
        plot_bgcolor="#1e1e2f",
        paper_bgcolor="#1e1e2f",
        font_color="#e0e0e0",
        title_font_color="#ffffff",
    )
    chart_score = json.dumps(fig_score, cls=plotly.utils.PlotlyJSONEncoder)

    # Chart 4: Top merchant categories with anomalies
    cat_stats = (
        df.groupby("merchant_category")
        .agg(total=("is_anomaly", "count"), anomalies=("is_anomaly", "sum"))
        .sort_values("anomalies", ascending=False)
        .head(10)
        .reset_index()
    )
    fig_cat = px.bar(
        cat_stats,
        x="merchant_category",
        y=["total", "anomalies"],
        title="Top Merchant Categories",
        barmode="group",
        labels={"value": "Count", "merchant_category": "Category"},
    )
    fig_cat.update_layout(
        plot_bgcolor="#1e1e2f",
        paper_bgcolor="#1e1e2f",
        font_color="#e0e0e0",
        title_font_color="#ffffff",
    )
    chart_cat = json.dumps(fig_cat, cls=plotly.utils.PlotlyJSONEncoder)

    # Table data
    anomalies = (
        Transaction.query.filter_by(dataset_id=dataset_id, is_anomaly=True)
        .order_by(Transaction.anomaly_score.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "dashboard.html",
        dataset=dataset,
        stats=stats,
        chart_time=chart_time,
        chart_dist=chart_dist,
        chart_score=chart_score,
        chart_cat=chart_cat,
        anomalies=anomalies,
    )


@main.route("/results/<int:dataset_id>")
def results(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    page = request.args.get("page", 1, type=int)
    per_page = 50
    show = request.args.get("show", "all")

    query = Transaction.query.filter_by(dataset_id=dataset_id)
    if show == "anomalies":
        query = query.filter_by(is_anomaly=True)

    pagination = query.order_by(Transaction.anomaly_score.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    transactions = pagination.items

    return render_template(
        "results.html",
        dataset=dataset,
        transactions=transactions,
        pagination=pagination,
        show=show,
    )


@main.route("/transaction/<int:txn_id>")
def transaction_detail(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    dataset = Dataset.query.get_or_404(txn.dataset_id)

    related = (
        Transaction.query.filter(
            Transaction.dataset_id == txn.dataset_id,
            Transaction.user_id == txn.user_id,
            Transaction.id != txn.id,
        )
        .order_by(Transaction.timestamp.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "transaction_detail.html", txn=txn, dataset=dataset, related=related
    )


@main.route("/export/<int:dataset_id>")
def export(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    txns = Transaction.query.filter_by(dataset_id=dataset_id).all()

    rows = [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "timestamp": t.timestamp.isoformat(),
            "merchant_category": t.merchant_category,
            "location": t.location,
            "user_id": t.user_id,
            "is_anomaly": t.is_anomaly,
            "anomaly_score": round(t.anomaly_score, 4),
        }
        for t in txns
    ]
    df = pd.DataFrame(rows)

    export_dir = current_app.config["UPLOAD_FOLDER"]
    export_path = os.path.join(export_dir, f"anomaly_report_{dataset_id}.csv")
    df.to_csv(export_path, index=False)

    return jsonify(
        {
            "status": "ok",
            "download": url_for(
                "static", filename=f"uploads/anomaly_report_{dataset_id}.csv"
            ),
        }
    )


@main.route("/delete/<int:dataset_id>", methods=["POST"])
def delete_dataset(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    Transaction.query.filter_by(dataset_id=dataset_id).delete()
    db.session.delete(dataset)
    db.session.commit()
    flash(f"Deleted analysis: {dataset.filename}", "success")
    return redirect(url_for("main.index"))


@main.route("/delete-all", methods=["POST"])
def delete_all():
    Transaction.query.delete()
    Dataset.query.delete()
    db.session.commit()
    flash("All analyses cleared.", "success")
    return redirect(url_for("main.index"))


@main.route("/api/stats/<int:dataset_id>")
def api_stats(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    txns = Transaction.query.filter_by(dataset_id=dataset_id).all()

    df = pd.DataFrame(
        [
            {
                "amount": t.amount,
                "is_anomaly": t.is_anomaly,
                "anomaly_score": t.anomaly_score,
            }
            for t in txns
        ]
    )
    stats = compute_stats(df)
    return jsonify(stats)
