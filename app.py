import streamlit as st
import pandas as pd

st.set_page_config(page_title="映画レコメンデーションシステム", layout="wide")

st.title("🎬 映画レコメンデーションシステム")
st.markdown("あなたの好きな映画を選んで、オススメの映画を見つけましょう！")

@st.cache_data
def load_data():
    try:
        movies_df = pd.read_csv('movies_100k.csv', sep='|', encoding='latin-1')
        if 'movie_id' not in movies_df.columns:
            pass
        movies_df = movies_df[['movie_id', 'movie_title']]
    except Exception as e:
        st.error(f"映画データの読み込みに失敗しました: {e}")
        return None, None, None

    try:
        ratings_df = pd.read_csv('ratings_100k.csv', sep=',')
    except Exception as e:
        st.error(f"評価データの読み込みに失敗しました: {e}")
        return None, None, None

    merged_df = pd.merge(ratings_df, movies_df, left_on='movieId', right_on='movie_id')
    
    return movies_df, ratings_df, merged_df

movies, ratings, data = load_data()

if movies is not None and data is not None:

    def get_popular_movies(n=5):
        movie_stats = data.groupby('movie_title').agg({'rating': ['mean', 'count']})
        movie_stats.columns = ['mean', 'count']
        
        qualified = movie_stats[movie_stats['count'] >= 50]
        
        top_movies = qualified.sort_values(by='mean', ascending=False).head(n)
        return top_movies

    @st.cache_data
    def get_correlation_matrix(df):
        user_movie_matrix = df.pivot_table(index='userId', columns='movie_title', values='rating')
        
        corr_matrix = user_movie_matrix.corr(method='pearson', min_periods=30)
        return corr_matrix

    with st.spinner('レコメンデーションエンジンの準備中...'):
        corr_matrix = get_correlation_matrix(data)
    
    st.sidebar.header("あなたの好みを選択")
    all_titles = movies['movie_title'].unique()
    selected_movies = st.sidebar.multiselect(
        "好きな映画を3つ以上選んでください",
        options=all_titles,
        default=[]
    )

    if st.button("オススメ映画を表示", type="primary"):
        st.divider()
        
        if len(selected_movies) == 0:
            st.warning("映画が選択されていません。ユーザー全体に人気の高い映画を表示します。")
            st.subheader("🏆 総合評価が高い名作トップ5")
            
            top_movies = get_popular_movies(5)
            
            for title, row in top_movies.iterrows():
                st.write(f"**{title}** (平均評価: {row['mean']:.2f} / 5.0)")

        elif len(selected_movies) < 3:
            st.error("精度向上のため、3つ以上の映画を選択してください。")
        
        else:
            st.success(f"選択された {len(selected_movies)} 作品の傾向に基づき分析しました。")
            st.subheader("🎯 あなたへのオススメ映画トップ5")

            sim_candidates = pd.Series(dtype='float64')

            for movie in selected_movies:
                if movie in corr_matrix.columns:
                    sim_scores = corr_matrix[movie].dropna()
                    
                    sim_candidates = sim_candidates.add(sim_scores, fill_value=0)
                else:
                    pass
            
            sim_candidates = sim_candidates.drop(selected_movies, errors='ignore')
            
            recommendations = sim_candidates.sort_values(ascending=False).head(5)
            
            if len(recommendations) > 0:
                for i, (title, score) in enumerate(recommendations.items(), 1):
                    st.write(f"{i}. **{title}**")
            else:
                st.info("データ不足により十分な推薦ができませんでした。もっとメジャーな映画を選んでみてください。")

else:
    st.info("CSVファイルを同じディレクトリに配置してリロードしてください。")