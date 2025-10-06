LLM Control: Alignment, Steering, and Agentic Learning
Source guide
The source provides a detailed classification and comparison of modern techniques used for LLM control and adaptation, grouping them based on when and what components are modified. These methods fall into three main categories: Parametric Training/Alignment, such as RLHF and DPO, which involve computationally heavy updates to the model's vast internal weights; Inference-Time Steering, exemplified by Activation Addition (ActAdd), which manipulates internal activations during the forward pass using lightweight steering vectors without altering the weights; and Agentic/Non-Parametric Learning, like Memento, which trains an external case-selection policy to guide the frozen LLM using a memory bank. A core theme uniting several control methods is the hypothesis that high-level features and concepts, such as sentiment or refusal, are represented as linear directions in the activation space, allowing them to be surgically manipulated or disabled. Fundamentally, the methods differ primarily in their target—weights, activations, or external memory—highlighting a strategic shift toward low-cost, continuous adaptation outside of traditional fine-tuning.

LLM Control: Alignment, Steering, and Agentic Learning
This is a comprehensive request spanning modern LLM control and adaptation techniques. The sources detail several distinct methods for influencing an LLM’s behaviour—from traditional parameter updating methods like fine-tuning and Reinforcement Learning (RL), to instantaneous, inference-time control methods like vector steering, and hybrid agentic learning paradigms like memory-based RL.
Here is a comprehensive comparison of the learning and steering methods mentioned in the sources, examining their mechanisms and how they relate to each other
--------------------------------------------------------------------------------

Comprehensive Comparison of LLM Learning and Steering Methods
The methods of influencing LLM behaviour found in the sources can be broadly categorised based on when the modification occurs (training/weight update vs. inference/activation manipulation) and what components are modified (model parameters vs. external memory/inputs).
Method Category
Primary Mechanism
Modification Target
When It Occurs
Key Examples from Sources
I. Parametric Training/Alignment
Gradient updates/Optimization
LLM Weights ($\pi_{\theta}$)
Training/Post-training
RLHF, Direct Preference Optimization (DPO, IPO, SLiC), Supervised Fine-Tuning (SFT) [1-5]
II. Inference-Time Steering
Direct manipulation of internal state
Activations (Residual Stream)
Inference/Forward Pass
Activation Addition (ActAdd), Steering Vectors, Directional Ablation [6-8]
III. Agentic/Non-Parametric Learning
Memory optimization via RL
External Case Policy/Memory ($\mu$)
Online/Continual Adaptation
Memento (Memory-based online RL/CBR) [9, 10]
I. Parametric Training and Alignment Methods (RL, DAP, Fine-Tuning)
These methods involve updating the vast number of parameters (weights) within the LLM, typically requiring significant computational resources and data [11].

1. Reinforcement Learning from Human Feedback (RLHF) and Frameworks
Reinforcement Learning (RL), particularly RLHF, is highlighted as a crucial step for aligning LLMs with human preferences, aiming to elicit desirable behaviours such as helpfulness and harmlessness [12]. The sources position RL as the core technology driving agent training in sophisticated, complex environments.
• Mechanism: RLHF typically first trains a proxy Reward Model (RM) based on human preferences (pairwise comparisons) [3]. Afterwards, offline RL (e.g., using PPO) is conducted to learn the policy ($\pi_{\theta}$) by maximizing the KL-regularized reward objective, which includes a pessimistic term to prevent distributional shift away from the reference policy ($\pi_{ref}$), often the SFT policy [3, 13].
• LLM Agent Environments (GEM/VERL): RL is fundamental to training LLM agents that learn from "experience gathered in complex, expressive environments" [14, 15]. GEM (General Experience Maker) is explicitly designed as a dedicated environment simulator, mirroring the API of popular RL environment suites like Gym, for training LLM agents in reasoning, code, math, and games [15-17]. Frameworks like VERL (Volcano Engine Reinforcement Learning for LLMs) and OAT provide flexible, efficient, and production-ready libraries for training LLM agents using diverse RL algorithms such as PPO, GRPO, GSPO, ReMax, RLOO, PRIME, DAPO, DrGRPO, KL_Cov, and Clip_Cov [16, 18-21].
• Performance: RL algorithms are continuously being refined for sample efficiency, notably through methods formalised under the Contextual Dueling Bandits (CDB) framework, such as SEA (Sample-Efficient Alignment) [22-25]. SEA leverages active exploration (like Thompson sampling) to achieve high sample efficiency, particularly in scenarios where human feedback is collected online or via crowdsourcing [26-28].
2. Direct Alignment from Preferences (DAP)
DAP methods simplify the alignment process compared to traditional RLHF.
• Mechanism: DAP methods like DPO (Direct Preference Optimization), IPO, and SLiC stabilize the alignment process by conducting contrastive supervised learning directly on preference data, acting as "direct optimizers" [4, 5, 29]. This avoids the instability often associated with RL optimizers [4].
• Relationship to RL: DAP is effectively a policy-based, model-free RL algorithm in the single-step preference-based RL framework, where the policy gradient update matches the gradient direction of contrastive DAP losses [30, 31].
3. Fine-Tuning (SFT)
Fine-tuning, including Supervised Fine-Tuning (SFT), is a conventional method that modifies the LLM's weights to maximize performance on a given metric [1, 7].
• Comparison to ActAdd: Fine-tuning is generally considered much more costly and may not elicit the same types of capabilities as activation engineering [32]. Fine-tuning is referred to as "ballistic" steering (steering the model once at train time), while Activation Addition is "online" steering (steering repeatedly at inference time) [33]. Furthermore, fine-tuning can compromise safety alignment even when the data is benign [34, 35].
II. Inference-Time Steering Methods (Activation Engineering)
These methods focus on controlling the LLM's output without changing the fundamental, frozen model weights, relying instead on manipulating the information flow (activations) during the forward pass [1].
1. Activation Addition (ActAdd) / Steering Vectors
Activation Addition (ActAdd) is a key technique introduced under the methodology of activation engineering [6, 7].
• Mechanism: ActAdd modifies the intermediate activation vectors (the "residual streams") during inference [7, 36]. It involves calculating a steering vector by finding the difference between the activations produced by a pair of contrasting prompts (e.g., "Love" minus "Hate") [6, 7, 37, 38]. This steering vector is then tactically added (with an injection coefficient $c$) to the residual stream at a specified layer ($l$) during the forward pass of a user prompt [6, 37, 39, 40].
• Goal and Impact: ActAdd provides inference-time control over high-level output properties like sentiment or topic [6, 7]. It achieves state-of-the-art results on tasks like negative-to-positive sentiment shift and detoxification, while importantly preserving the model’s general capabilities on off-target tasks (e.g., factual knowledge benchmarks like ConceptNet) [6, 7, 41-43].
• Efficiency and Cost: ActAdd is lightweight, requires no gradient descent or machine optimization, and can work effectively with just two data points (the contrast pair), enabling rapid iteration over steering [6, 7, 32].
• Comparison to Prompt Engineering: ActAdd may elicit capabilities that prompting cannot, as activation additions are continuous (can be continuously weighted by coefficient $c$) unlike discrete token inputs, and they do not consume token space in the context window [44-48].
2. Directional Ablation and Weight Orthogonalization
These methods utilize the same underlying principles as ActAdd but are typically used for safety control or model interpretation (un-learning/disabling a feature).
• Underlying Principle: Both activation addition and ablation rely on the hypothesis that features or concepts (like sentiment, refusal, or truth) are represented as linear directions in the activation space (the "linear representation hypothesis") [49-51].
• Mechanism (Ablation): Refusal behaviour, for instance, is mediated by a single direction in the residual stream [52, 53]. Directional Ablation surgically disables a feature by actively "zeroing out" the component of every residual stream activation along that specific direction ($\hat{r}$) across all layers and token positions [8, 54].
• Weight Orthogonalization: This is the equivalent method implemented as a direct, rank-one modification to the model weights (e.g., MLP out matrices or embedding matrix) [55-57]. This allows the refusal behaviour to be disabled permanently without requiring inference-time activation hooking [55, 56]. This process is highly surgical and often causes minimal degradation to general model capabilities on benchmarks like MMLU, ARC, and GSM8K [58-60].
III. Agentic/Non-Parametric Learning (Memento)
This category introduces a way for LLM agents to continually adapt and improve performance without incurring the cost of modifying the underlying LLM's vast parameter set.
Memento: Memory-Based Online Reinforcement Learning
Memento is introduced as a novel learning paradigm for adaptive LLM agents that eliminates the need for fine-tuning the underlying LLMs [9, 10].
• Mechanism: Memento formalises the agent's actions as a Memory-augmented Markov Decision Process (M-MDP) [9, 10, 61]. The core idea is to shift learning away from updating the LLM parameters (which are fixed/frozen) and instead use online RL (specifically, soft Q-learning) to train a neural case-selection policy ($\mu$) [9, 10, 62].
• Data and Adaptation: Past experiences, including successes and failures, are stored in an external episodic memory (Case Bank) [9, 63-65]. Policy improvement (or adaptation) is achieved by efficiently reading (retrieving) the most relevant cases from this memory, which are then used to guide the LLM's decision-making (planning/action) for the current task [9, 10, 66, 67]. The policy is continually updated via a memory rewriting mechanism based on environmental feedback [9, 10].
• Comparison to Fine-Tuning: Memento addresses the challenge of building generalist agents that learn continually without the computationally intensive cost of gradient updates (parametric approaches) [11, 63]. It provides a low-cost, scalable pathway for real-time adaptation and open-ended skill acquisition [9, 10].

--------------------------------------------------------------------------------
Are These Methods Actually the Same Under the Hood?
No, fundamentally, these methods target different components of the LLM pipeline, though they are united by the goal of eliciting or shaping model capability, and they often exploit the same mathematical properties of deep neural networks.
The Parametric vs. Non-Parametric Divide
The largest distinction is between methods that modify the weights of the LLM (Parametric/Training methods, Category I) and those that modify the activations or external context/policy (Inference-Time/Agentic methods, Categories II and III) [63, 64].

1. RL/DAP (Category I): These are classic machine learning training methodologies. They define a loss function (e.g., PPO loss, DPO loss) and use gradient descent (the "backward pass") to physically change the numerical values of the millions or billions of parameters ($\theta$) within the LLM layers [1, 3, 32]. The learning is "ballistic" [33].
2. Activation Engineering (Category II): This bypasses the weight update entirely. It relies on the model weights remaining frozen [32, 68]. Instead of altering $\theta$, it alters the residual stream vector $x$ during the forward pass (inference) [7, 36]. This control is instantaneous and ephemeral (it doesn't last beyond the current inference call, unless implemented as a weight edit/orthogonalization) [7, 33].
3. Memento (Category III): This approach also keeps the core LLM weights fixed (non-parametric) but uses RL principles (Q-learning) to learn an optimal input strategy (case retrieval policy $\mu$) from an external memory bank [9, 10, 62]. The adaptation happens not by changing the LLM itself, but by learning how to expertly construct the context (input) provided to the frozen LLM, utilizing external memory updating instead of gradient updating on the LLM [63, 66].
The Role of Linear Representations
While different in implementation, the effectiveness of Activation Engineering (ActAdd and Ablation) and certain aspects of safety alignment (where the refusal mechanism is localized to a linear direction) share a deep reliance on the geometric properties of the LLM's internal representation space [49, 50].
• The success of Activation Addition provides experimental evidence for the hypothesis that neural networks represent features (like love/hate, topic, refusal) as linear directions in activation space [49, 50, 69].
• Activation engineering exploits this linearity by calculating the difference between two contrasting inputs, yielding a vector that defines this feature direction [37, 38].
• The fact that refusal behaviour can be successfully disabled by directionally ablating a single vector further demonstrates that complex behaviours resulting from extensive RLHF alignment are chemically mediated by a single linear subspace [52-54].
In essence, while RL/DAP creates or aligns these internal representations by updating weights, Activation Engineering and Ablation methods demonstrate they are easily controlled or removed once established, confirming that the high-level capabilities of the LLM reside in surprisingly simple, manipulable linear subspaces within the activation geometry [46, 50, 70].
