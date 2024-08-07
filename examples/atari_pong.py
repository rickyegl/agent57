import gym
from keras.optimizers import Adam

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from agent.agent57 import ActorUser
from agent.policy import EpsilonGreedy, AnnealingEpsilonGreedy
from agent.memory import PERRankBaseMemory, PERProportionalMemory
from agent.model import InputType, LstmType, UvfaType
from agent.model import DQNImageModel, R2D3ImageModel
from agent.common import seed_everything
from agent.callbacks import LoggerType

from agent.main_runner import run_gym_dqn, run_play, run_replay, run_gym_agent57

from agent.processor import AtariPong


seed_everything(42)
ENV_NAME = "ALE/Pong-v5"
episode_save_dir = "tmp_{}.".format(ENV_NAME)


def create_parameter(env, nb_steps):
    
    processor = AtariPong(end_count=5)

    image_model = DQNImageModel()
    #image_model = R2D3ImageModel()

    kwargs = {
        "input_shape": processor.image_shape, 
        "input_type": InputType.GRAY_2ch,
        "input_model": image_model,
        "nb_actions": processor.nb_actions,
        #"nb_actions": env.action_space.n,

        "memory": "PERRankBaseMemory",
        "memory_kwargs": {
            "capacity": 400_000,
            "alpha": 1.0,          # PERの確率反映率
            "beta_initial": 0.0,   # IS反映率の初期値(1.0が最大)
            "beta_steps": nb_steps,  # IS反映率の上昇step数
            "enable_is": True,     # ISを有効にするかどうか
        },
        
        "optimizer_ext": Adam(lr=0.0001, epsilon=0.0001),
        "optimizer_int": Adam(lr=0.0001, epsilon=0.0001),
        "optimizer_rnd": Adam(lr=0.0005, epsilon=0.0001),
        "optimizer_emb": Adam(lr=0.0005, epsilon=0.0001),

        # NN
        "batch_size": 16,     # batch_size
        "input_sequence": 4,         # 入力フレーム数
        "dense_units_num": 256,       # dense層のユニット数
        "enable_dueling_network": True,
        "lstm_type": LstmType.STATELESS,           # 使用するLSTMアルゴリズム
        "lstm_units_num": 256,             # LSTMのユニット数
        "lstmful_input_length": 2,       # ステートフルLSTMの入力数
        "burnin_length": 0,        # burn-in期間

        # train
        "memory_warmup_size": 6250,    # 初期のメモリー確保用step数(学習しない)
        "target_model_update_interval": 1500,  # target networkのupdate間隔
        "enable_double_dqn": True,
        "enable_rescaling": False,   # rescalingを有効にするか
        "reward_multisteps": 3,    # multistep reward

        "demo_memory": "PERProportionalMemory",
        "demo_memory_kwargs": {
            "capacity": 100_000,
            "alpha": 0.8,
        },
        "demo_episode_dir": episode_save_dir,
        "demo_ratio_initial": 1.0,
        "demo_ratio_final": 1.0/512.0,
        "demo_ratio_steps": nb_steps,

        #"episode_memory": "PERProportionalMemory",
        "episode_memory_kwargs": {
            "capacity": 5_000,
            "alpha": 0.8,
        },
        "episode_ratio": 1.0/128.0,

        # uvfa
        "uvfa_ext": [
            UvfaType.ACTION,
            UvfaType.REWARD_EXT,
            UvfaType.REWARD_INT,
            UvfaType.POLICY,
        ],
        "uvfa_int": [
            UvfaType.ACTION,
            UvfaType.REWARD_EXT,
            UvfaType.REWARD_INT,
            UvfaType.POLICY,
        ],

        # intrinsic_reward
        "enable_intrinsic_actval_model": True,

        # intrinsic_reward
        "policy_num": 8,
        "ucb_epsilon": 0.5,
        "ucb_window_size": 60,

        "processor": processor,
        "step_interval": 1,
        "enable_add_episode_end_frame": False,
    }

    return kwargs


#--------------------------------------------


def run_dqn(enable_train):
    env = gym.make(ENV_NAME)

    # ゲーム情報
    print("action_space      : " + str(env.action_space))
    print("observation_space : " + str(env.observation_space))
    print("reward_range      : " + str(env.reward_range))
    nb_steps = 1_750_000

    kwargs = create_parameter(env, nb_steps)
    kwargs["action_policy"] = AnnealingEpsilonGreedy(
        initial_epsilon=1.0,      # 初期ε
        final_epsilon=0.01,        # 最終状態でのε
        exploration_steps=100_000  # 初期→最終状態になるまでのステップ数
    )

    run_gym_dqn(
        enable_train,
        env,
        ENV_NAME,
        kwargs,
        nb_steps=nb_steps,
        nb_time=60*60*18,   # 18h
        logger_type=LoggerType.TIME,
        log_interval=60*20,  # 20m
        test_env=env,
        test_episodes=10,
        movie_save=False,
    )
    env.close()
    
#--------------------------------------------


class MyActor(ActorUser):
    def getPolicy(self, actor_index, actor_num):
        return EpsilonGreedy(0.1)

    def fit(self, index, agent):
        env = gym.make(ENV_NAME)
        agent.fit(env, visualize=False, verbose=0)
        env.close()

class MyActor1(MyActor):
    def getPolicy(self, actor_index, actor_num):
        return EpsilonGreedy(0.01)

class MyActor2(MyActor):
    def getPolicy(self, actor_index, actor_num):
        return EpsilonGreedy(0.05)

class MyActor3(MyActor):
    def getPolicy(self, actor_index, actor_num):
        return EpsilonGreedy(0.1)

class MyActor4(MyActor):
    def getPolicy(self, actor_index, actor_num):
        return EpsilonGreedy(0.2)

def create_env():
    return gym.make(ENV_NAME)


def run_agent57(enable_train):
    env = gym.make(ENV_NAME)

    # ゲーム情報
    print("action_space      : " + str(env.action_space))
    print("observation_space : " + str(env.observation_space))
    print("reward_range      : " + str(env.reward_range))
    nb_steps = 1_750_000

    kwargs = create_parameter(env, nb_steps)

    kwargs["actors"] = [MyActor1]
    #kwargs["actors"] = [MyActor1, MyActor3]
    #kwargs["actors"] = [MyActor1, MyActor2, MyActor3, MyActor4]
    kwargs["sync_actor_model_interval"] = 50  # learner から model を同期する間隔

    run_gym_agent57(
        enable_train,
        env,
        ENV_NAME,
        kwargs,
        nb_trains=1_750_000,
        nb_time=60*60*18,  # 18h
        logger_type=LoggerType.TIME,
        log_interval=60*20,  # 20m
        test_env=create_env,
        is_load_weights=False,
        movie_save=False,
    )
    env.close()


if __name__ == '__main__':
    
    # エピソードを作成、保存
    if False:
        env = gym.make(ENV_NAME)
        kwargs = create_parameter(env, 0)
        run_play(env, episode_save_dir, kwargs["processor"], zoom=3)

    # エピソードを再生(確認用)
    if False:
        run_replay(episode_save_dir)

    # SingleActorレーニング
    if False:
        run_dqn(enable_train=True)
        #run_dqn(enable_train=False)  # test only

    # 複数Actorレーニング
    if True:
        run_agent57(enable_train=True)
        #run_agent57(enable_train=False)  # test only

