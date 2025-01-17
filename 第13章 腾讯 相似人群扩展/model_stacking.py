import pandas as pd
from sklearn.model_selection import KFold
from catboost import Pool, CatBoostClassifier
from sklearn.metrics import roc_auc_score


def read_data():
    """

    :return:
    """

    train = pd.read_csv('preprocess/train_sample.csv')
    test = pd.read_csv('preprocess/test_sample.csv')

    train['lightgbm'] = pd.read_csv("result/train_lightgbm.csv")['0'].values
    test['lightgbm'] = pd.read_csv("result/test_lightgbm.csv")['0'].values

    train['xgboost'] = pd.read_csv("result/train_xgboost.csv")['0'].values
    test['xgboost'] = pd.read_csv("result/test_xgboost.csv")['0'].values




    train[cat_features] = train[cat_features].astype(str)
    test[cat_features] = test[cat_features].astype(str)

    train[text_features] = train[text_features].astype(str)
    test[text_features] = test[text_features].astype(str)
    return train, test

def train_predict(train, test):
    """

    :param train:
    :param test:
    :return:
    """
    truth_test = pd.read_csv('preprocess/test_truth_sample.csv')['label'].values


    label = 'label'
    feature_names = train.columns.tolist()
    feature_names.remove(label)
    feature_names = cat_features + text_features + ['aid', 'uid'] + ['lightgbm', 'xgboost']
    kf = KFold(n_splits=5, random_state=2020, shuffle=True)
    prediction_test = 0
    prediction_train = pd.Series()
    score_train = []
    for train_part_index, eval_index in kf.split(train[text_features], train[label]):

        learn_pool = Pool(
            train[feature_names].loc[train_part_index],
            train[label].loc[train_part_index],
            text_features=text_features,
            cat_features= cat_features,
            feature_names=feature_names
        )
        test_pool = Pool(
            train[feature_names].loc[eval_index],
            train[label].loc[eval_index],
            text_features=text_features,
            cat_features= cat_features,
            feature_names=feature_names
        )

        model = CatBoostClassifier(iterations=100, learning_rate=0.1, eval_metric='AUC', task_type='GPU')
        model.fit(learn_pool, eval_set=test_pool, verbose=50)
        score_train.append(model.best_score_['validation']['AUC'])
        prediction_test += model.predict_proba(test[feature_names])[:, 1]
        prediction_train = prediction_train.append(pd.Series(
            model.predict_proba(train[feature_names].loc[eval_index])[:, 1], index=eval_index))
        print(roc_auc_score(truth_test, prediction_test))
    print(score_train, sum(score_train)/5)
    # [0.7065661549568176, 0.7076177597045898, 0.7220486998558044, 0.7044380605220795, 0.698743462562561] 0.7078828275203705print(roc_auc_score(truth_test, prediction_test/5))
    # 0.6744532384583376
    pd.Series(prediction_train.sort_index().values).to_csv("result/train_catboost_stacking.csv", index=False)
    pd.Series(prediction_test / 5).to_csv("result/test_catboost_stacking.csv", index=False)
    return
text_features = ['appIdAction', 'appIdInstall', 'ct', 'interest1',
                 'interest2', 'interest3', 'interest4', 'interest5', 'kw1',
                 'kw2', 'kw3', 'marriageStatus', 'os', 'topic1', 'topic2', 'topic3']

cat_features = ['LBS', 'adCategoryId', 'advertiserId', 'age', 'campaignId',
                'carrier', 'consumptionAbility', 'creativeId', 'creativeSize', 'education',
                'gender', 'house', 'productId', 'productType']


if __name__ == "__main__":

    # 读取数据
    train, test = read_data()
    # 模型训练与预测
    train_predict(train, test)