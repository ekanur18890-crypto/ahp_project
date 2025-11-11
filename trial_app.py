import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO

#======================================PAGE CONFIGURATION=============================================================

st.set_page_config(page_title="AHP App", page_icon="⚙️", layout="wide")

st.title("⚙️ AHP Priority")
st.write("AHP Priority merupakan aplikasi berbasis metode Analytical Hierarchy Process (AHP) yang dirancang untuk mendukung proses pengambilan keputusan multi-kriteria. Aplikasi ini membantu pengguna dalam melakukan pembobotan kriteria dan perankingan alternatif secara terstruktur.") 
st.write("Pilih fitur yang Anda inginkan pada tombol di bawah ini.")

#=======================================NAVIGATION BUTTONS==================================================
col1, col2 = st.columns(2)
with col1:
    weighting_btn = st.button("🎯 Weighting Criteria", width="stretch")
with col2:
    ranking_btn = st.button("🏆 Ranking Alternative", width="stretch")

if weighting_btn:
    st.session_state["page"] = "weighting"
if ranking_btn:
    st.session_state["page"] = "ranking"
if "page" not in st.session_state:
    st.session_state["page"] = "home"

st.write("Aplikasi AHP ini juga tersedia dalam template Excel.")
file_path = "ahp_full_template.xlsx"
with open(file_path, "rb") as f:
    full_template = f.read()
    
st.download_button(
    label="📥 Download full template",
    data=full_template,
    file_name="ahp_full_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
    
#======================================WEIGHTING CRITERIA=============================================================
if st.session_state["page"] == "weighting":
    st.header("🎯 Weighting Criteria")

    # Membuat kolom untuk input kriteria
    st.subheader("Langkah 1: Menentukan Input Kriteria")
    criteria = st.text_input("Masukkan kriteria (gunakan koma sebagai pemisah):", "Kriteria 1, Kriteria 2, Kriteria 3").split(",")
    criteria = [c.strip() for c in criteria if c.strip()]

    if len(criteria) < 2:
        st.warning("Masukkan minimal 2 kriteria.")
        st.stop()

    # Membuat matriks perbandingan berpasangan kriteria
    st.subheader("Langkah 2: Perbandingan Berpasangan Antar Kriteria")
    st.write("Gunakan template excel untuk menentukan perbandingan berpasangan")
    
    file_loc = "pairwise_template.xlsx"
    with open(file_loc, "rb") as f:
        file_template = f.read()
    
    st.download_button(
        label="📥 Download template",
        data=file_template,
        file_name="pairwise_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    criteria_matrix = np.ones((len(criteria), len(criteria)))
    criteria_df = pd.DataFrame(criteria_matrix, columns=criteria, index=criteria)

    # Membuat tabel untuk input data kriteria
    st.markdown("Masukkan data kriteria pada tabel berikut:")

    edited_df = st.data_editor(criteria_df, key="criteria_table", num_rows="fixed")
    
    # Update reciprocals secara otomatis
    for i in range(len(criteria)):
        for j in range(len(criteria)):
            if i == j:
                edited_df.iloc[i, j] = 1.0
            elif edited_df.iloc[i, j] != 0:
                edited_df.iloc[j, i] = round(1 / edited_df.iloc[i, j], 3)

    # Menghitung bobot kriteria
    matrix = edited_df.to_numpy().astype(float)
    
    # Normalisasi matriks
    col_sum = matrix.sum(axis=0)
    normalized_matrix = matrix / col_sum

    # Menghitung vektor prioritas
    weights = normalized_matrix.mean(axis=1)
    weights = weights / weights.sum()  # ensure they sum to 1

    # Membuat tabel untuk menampilkan hasil
    weights_df = pd.DataFrame({
    "Kriteria": criteria,
    "Bobot": np.round(weights, 4)
    })
    
    # Menyimpan hasil perhitungan bobot kriteria
    st.session_state["criteria_names"] = criteria
    st.session_state["criteria_weights"] = weights
    
    # Perhitungan Consistency Ratio
    weighted_sum = np.dot(matrix, weights)
    consistency_vector = weighted_sum / weights
    lambda_max = np.mean(consistency_vector)
    n = len(criteria)
    CI = (lambda_max - n) / (n - 1)
    
    # Nilai Random Index (RI)
    RI_dict = {1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
    RI = RI_dict.get(n, 1.49)  # default max for n > 10
    CR = CI / RI if RI != 0 else 0
    
    # Menampilkan tabel final
    st.write("Matriks perbandingan berpasangan")
    st.dataframe(pd.DataFrame(matrix, index=criteria, columns=criteria).style.format("{:.3f}"))
    
    st.write("Matriks normalisasi")
    st.dataframe(pd.DataFrame(normalized_matrix, index=criteria, columns=criteria).style.format("{:.3f}"))
    
    st.subheader("Langkah 3. Menentukan Bobot Kriteria")
    st.table(weights_df.style.hide(axis='index'))
    
    # Menampilkan consistency ratio
    st.subheader("Langkah 4: Cek Konsistensi")
    st.write(f"λ_max = {lambda_max:.4f}")
    st.write(f"CI = {CI:.4f}")
    st.write(f"CR = {CR:.4f}")

    if CR < 0.10:
        st.success("✅ Matriks perbandingan berpasangan konsisten (CR < 0.1)")
    else:
        st.error("⚠️ Matriks tidak konsisten (CR ≥ 0.1)")
        
        
    # Membuat file Excel untuk menampilkan hasil perhitungan
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        pd.DataFrame(matrix, index=criteria, columns=criteria).to_excel(writer, sheet_name='Perbandingan Berpasangan')
        pd.DataFrame(normalized_matrix, index=criteria, columns=criteria).to_excel(writer, sheet_name='Matriks Normalisasi')
        weights_df.to_excel(writer, sheet_name='Bobot', index=False)
        summary_df = pd.DataFrame({
            'Lambda Max': [lambda_max],
            'CI': [CI],
            'CR': [CR]
        })
    summary_df.to_excel(writer, sheet_name='Konsistensi', index=False)
    writer.close()

    # Membuat tombol untuk download Excel
    st.write("Halaman ini akan di-reset saat Anda pindah halaman. Pastikan download hasil perhitungan pada Excel berikut.")
    st.download_button(
    label="📥 Download Hasil",
    data=output.getvalue(),
    file_name="Hasil_Bobot_Kriteria.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
    
# ===================================== RANKING ALTERNATIVE ========================================================
if st.session_state["page"] == "ranking":
    st.header("🏆 Ranking Alternatives")

    # Input alternatives
    st.subheader("Langkah 1: Menentukan Input Alternatif")
    alternatives = st.text_input("Masukkan alternatif (gunakan koma sebagai pemisah):", "Alt 1, Alt 2, Alt 3").split(",")
    alternatives = [a.strip() for a in alternatives if a.strip()]

    if len(alternatives) < 2:
        st.warning("Masukkan minimal 2 alternatif")
        st.stop()

    # Pemilihan Bobot Kriteria
    st.subheader("Langkah 2: Pilih Bobot Kriteria")

    use_prev = st.radio(
    "Apakah anda ingin menggunakan bobot kriteria pada perhitungan sebelumnya?",
    ("Ya", "Tidak, input manual")
)

    if use_prev == "Ya":
        if "criteria_names" in st.session_state and "criteria_weights" in st.session_state:
            criteria = st.session_state["criteria_names"]
            weights = st.session_state["criteria_weights"]
            st.success("✅ Memuat data dan kriteria pada perhitungan sebelumnya")
            weights_df = pd.DataFrame({
                "Criteria": criteria,
                "Weight": np.round(weights, 4)
            })
            st.dataframe(weights_df, width="stretch")
        else:
            st.warning("Tidak ada data yang tersimpan. Mohon lakukan perhitungan bobot.")
            st.stop()
    else:
        
        # Manual input of criteria and weights
        st.subheader("Input Manual Kriteria dan Bobot")
        criteria = st.text_input("Masukkan kriteria (gunakan koma sebagai pemisah):", "Kriteria 1, Kriteria 2, Kriteria 3").split(",")
        criteria = [c.strip() for c in criteria if c.strip()]
        weights_input = st.text_input("Masukkan bobot (gunakan koma sebagai pemisah, harus sesuai dengan jumlah kriteria):", "0.3, 0.5, 0.2")

        try:
            weights = np.array([float(w.strip()) for w in weights_input.split(",")])
            weights = weights / np.sum(weights)
        except:
            st.warning("Masukkan nilai bobot yang valid.")
            st.stop()  

    # Perbandingan Berpasangan untuk setiap Kriteria
    st.subheader("Langkah 3: Perbandingan Berpasangan untuk Alternatif")
    st.write("Gunakan template excel untuk menentukan perbandingan berpasangan")
    
    file_loc = "pairwise_template.xlsx"
    with open(file_loc, "rb") as f:
        file_template = f.read()
    
    st.download_button(
        label="📥 Download template",
        data=file_template,
        file_name="pairwise_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    alt_scores = {}
    consistency_data = []

    for c in criteria:
        st.markdown(f"#### Kriteria: {c}")
        matrix = np.ones((len(alternatives), len(alternatives)))
        df = pd.DataFrame(matrix, columns=alternatives, index=alternatives)
        edited_df = st.data_editor(df, key=f"{c}_table", num_rows="fixed")

        # Ensure reciprocal consistency
        for i in range(len(alternatives)):
            for j in range(len(alternatives)):
                if i == j:
                    edited_df.iloc[i, j] = 1.0
                elif edited_df.iloc[i, j] != 0:
                    edited_df.iloc[j, i] = round(1 / edited_df.iloc[i, j], 3)

        matrix = edited_df.to_numpy().astype(float)

        # Perhitungan bobot
        n = matrix.shape[0]
        col_sum = matrix.sum(axis=0)
        norm_matrix = matrix / col_sum
        w = norm_matrix.mean(axis=1)
        w = w / w.sum()

        # Perhitungan Consistency Ratio
        Aw = np.dot(matrix, w)
        lambda_max = np.mean(Aw / w)
        CI = (lambda_max - n) / (n - 1)
        RI_dict = {1:0, 2:0, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
        RI = RI_dict.get(n, 1.49)
        CR = CI / RI if RI != 0 else 0

        consistency_data.append((c, round(CR, 4)))
        alt_scores[c] = w

    # Final ranking
    alt_matrix = np.column_stack([alt_scores[c] for c in criteria])
    final_scores = np.dot(alt_matrix, weights)
    ranking_df = pd.DataFrame({
        "Alternatif": alternatives,
        "Final Score": np.round(final_scores, 4)
    }).sort_values(by="Final Score", ascending=False)

    st.subheader("🏁 Hasil Final Ranking")
    st.dataframe(ranking_df, width="stretch")

    # Menampilkan hasil consistency ratio
    st.subheader("📏 Consistency Ratio untuk setiap Kriteria")
    consistency_df = pd.DataFrame(consistency_data, columns=["Kriteria", "CR"])
    st.dataframe(consistency_df, width="stretch")

    # Download hasil dalam Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        ranking_df.to_excel(writer, index=False, sheet_name="Hasil Ranking")
        consistency_df.to_excel(writer, index=False, sheet_name="Consistency Ratio")
    
    st.write("Halaman ini akan di-reset saat Anda pindah halaman. Pastikan download hasil perhitungan pada Excel berikut.")
    st.download_button(
        label="📥 Download Hasil",
        data=output.getvalue(),
        file_name="Hasil_Ranking_Alternatif.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown(
    """
    <div style='text-align: center; color: rgba(0, 0, 0, 0.5); font-size: 15px; margin-top: 50px;'>
        Kelompok Riset Microgrid<br>2025
    </div>
    
    <div style='text-align: center; color: rgba(0, 0, 0, 0.5); font-size: 17px; margin-top: 50px;'>
        Pusat Riset Teknologi Kelistrikan<br>Badan Riset dan Inovasi Nasional
    </div>
    """,
    unsafe_allow_html=True
)
