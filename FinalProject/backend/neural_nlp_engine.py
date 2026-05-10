import re
import random
from collections import Counter
from typing import List, Dict, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


RANDOM_SEED = 7
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

INTENT_LABELS = [
    "next_destination",
    "destination_reason",
    "current_location_reason",
    "next_location_prediction",
    "validity_check",
    "probability_to_location",
    "student_type",
    "schedule_query",
    "sport_query",
    "time_query",

    # New communication/social intents
    "wellbeing_query",
    "identity_query",
    "social_presence_query",
    "absence_reason",
    "miss_class_request",
    "user_instruction",
]

LABEL2ID = {label: i for i, label in enumerate(INTENT_LABELS)}
ID2LABEL = {i: label for label, i in LABEL2ID.items()}

PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"


def normalize_text(text: str) -> str:
    text = text.lower().strip()

    # Remove punctuation but keep colon because time values like 09:40 need it.
    text = re.sub(r"[^\w\s:]", "", text)

    text = re.sub(r"\s+", " ", text)
    return text


def simple_tokenize(text: str) -> List[str]:
    return normalize_text(text).split()


TEMPLATES = {
    "next_destination": [
        "where are you going next",
        "where are you going",
        "where will you go next",
        "what is your next destination",
        "where are you headed",
        "where do you go after this",
        "what place comes next",
    ],
    "destination_reason": [
        "why are you going there",
        "why are you headed there",
        "why is that your next stop",
        "what is the reason you are going there",
        "why will you go there next",
        "why are you moving to that location",
    ],
    "current_location_reason": [
        "why are you here",
        "why are you at this location",
        "why does it make sense that you are here",
        "what explains your current location",
        "why are you in this place right now",
    ],
    "next_location_prediction": [
        "where are you likely to be next",
        "where will you probably be next",
        "predict your next location",
        "what is your most likely next location",
        "where do you probably end up next",
    ],
    "validity_check": [
        "are you in the right place",
        "are you supposed to be here",
        "are you where you should be",
        "does this location make sense",
        "should you be somewhere else",
    ],
    "probability_to_location": [
        "what is the probability you go there",
        "how likely are you to go there",
        "what are the chances you move there",
        "estimate the probability of going there",
        "how probable is that destination",
    ],
    "student_type": [
        "what type of student are you",
        "are you an athlete",
        "are you a copa student",
        "are you a regular student",
        "what student group do you belong to",
    ],
    "schedule_query": [
        "what is your schedule today",
        "tell me your schedule",
        "what are you doing today",
        "what is your day like",
        "where are you during this time slot",
    ],
    "sport_query": [
        "what sport do you play",
        "are you in a sport",
        "what is your sport",
        "do you play track",
        "are you a track athlete",
    ],
    "time_query": [
        "what time is it",
        "what is the current time slot",
        "what time slot are you in",
        "what period is this",
        "what is the simulation time",
    ],
        "wellbeing_query": [
        "how are you",
        "how are you feeling",
        "are you okay",
        "how do you feel today",
        "are you tired",
        "how is your day going",
        "are you doing alright",
    ],
    "identity_query": [
        "who are you",
        "tell me about yourself",
        "what is your name",
        "what agent are you",
        "introduce yourself",
        "who am i talking to",
    ],
    "social_presence_query": [
        "who are you with",
        "who is with you",
        "are you with anyone",
        "who else is here",
        "which agents are near you",
        "who is in the same location as you",
    ],
    "absence_reason": [
        "why are you not in the library",
        "why are you not at track",
        "why are you not in student center",
        "why are you not at west penn",
        "why are you not in academic hall",
        "why are you somewhere else",
        "why are you not in class",
        "why are you not at your assigned location",
    ],
    "miss_class_request": [
        "can we miss class",
        "should we skip class",
        "can you skip class",
        "do you want to miss class",
        "should we not go to class",
        "can we avoid class today",
    ],
    "user_instruction": [
        "please go to village park next",
        "could you go to the library next",
        "go to student center next please",
        "it is important that you go to west penn",
        "could you do me a favor and go to academic hall",
        "i order you to go to track",
        "just go to the library",
        "because i want you to go to student center",
    ],
}


def generate_training_data(n_per_intent: int = 80) -> Tuple[List[str], List[str]]:
    filler_prefixes = [
        "",
        "hey ",
        "quick question ",
        "can you tell me ",
        "please tell me ",
        "i want to know ",
    ]

    filler_suffixes = [
        "",
        "?",
        " please",
        " right now",
        " if possible",
    ]

    texts = []
    labels = []

    for intent, examples in TEMPLATES.items():
        for _ in range(n_per_intent):
            text = random.choice(examples)
            text = random.choice(filler_prefixes) + text + random.choice(filler_suffixes)

            if random.random() < 0.12:
                text = text.replace("you", "u")
            if random.random() < 0.10:
                text = text.replace("going", "headed")
            if random.random() < 0.08:
                text = text.capitalize()

            texts.append(normalize_text(text))
            labels.append(intent)

    return texts, labels


def build_vocab(texts: List[str], min_freq: int = 1) -> Dict[str, int]:
    counter = Counter()

    for text in texts:
        counter.update(simple_tokenize(text))

    vocab = {
        PAD_TOKEN: 0,
        UNK_TOKEN: 1,
    }

    for token, freq in counter.items():
        if freq >= min_freq:
            vocab[token] = len(vocab)

    return vocab


def encode_tokens(tokens: List[str], vocab: Dict[str, int], max_len: int) -> Tuple[List[int], int]:
    ids = [vocab.get(token, vocab[UNK_TOKEN]) for token in tokens][:max_len]
    length = len(ids)

    if len(ids) < max_len:
        ids += [vocab[PAD_TOKEN]] * (max_len - len(ids))

    return ids, max(length, 1)


class IntentDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len=24):
        self.texts = texts
        self.labels = [LABEL2ID[label] for label in labels]
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        tokens = simple_tokenize(self.texts[idx])
        ids, length = encode_tokens(tokens, self.vocab, self.max_len)

        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "length": torch.tensor(length, dtype=torch.long),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
            "text": self.texts[idx],
        }


class GRUIntentClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, input_ids, lengths):
        embedded = self.embedding(input_ids)

        packed = nn.utils.rnn.pack_padded_sequence(
            embedded,
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )

        _, hidden = self.gru(packed)
        logits = self.classifier(hidden[-1])

        return logits


class AttentionBiGRUIntentClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.bigru = nn.GRU(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.attention_layer = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, input_ids, lengths, return_attention=False):
        embedded = self.embedding(input_ids)

        packed = nn.utils.rnn.pack_padded_sequence(
            embedded,
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )

        packed_output, _ = self.bigru(packed)
        outputs, _ = nn.utils.rnn.pad_packed_sequence(packed_output, batch_first=True)

        batch_size, seq_len, _ = outputs.size()

        mask = torch.arange(seq_len, device=lengths.device).unsqueeze(0) < lengths.unsqueeze(1)

        attention_scores = self.attention_layer(outputs).squeeze(-1)
        attention_scores = attention_scores.masked_fill(~mask, -1e9)

        attention_weights = torch.softmax(attention_scores, dim=1)

        context = torch.bmm(attention_weights.unsqueeze(1), outputs).squeeze(1)
        logits = self.classifier(context)

        if return_attention:
            return logits, attention_weights

        return logits


def train_one_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0.0

    for batch in loader:
        input_ids = batch["input_ids"].to(DEVICE)
        lengths = batch["length"].to(DEVICE)
        labels = batch["label"].to(DEVICE)

        optimizer.zero_grad()
        logits = model(input_ids, lengths)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * input_ids.size(0)

    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate_model(model, loader, criterion):
    model.eval()

    total_loss = 0.0
    predictions = []
    golds = []

    for batch in loader:
        input_ids = batch["input_ids"].to(DEVICE)
        lengths = batch["length"].to(DEVICE)
        labels = batch["label"].to(DEVICE)

        logits = model(input_ids, lengths)
        loss = criterion(logits, labels)

        total_loss += loss.item() * input_ids.size(0)
        predictions.extend(torch.argmax(logits, dim=1).cpu().tolist())
        golds.extend(labels.cpu().tolist())

    return {
        "loss": total_loss / len(loader.dataset),
        "accuracy": accuracy_score(golds, predictions),
        "macro_f1": f1_score(golds, predictions, average="macro"),
    }


def train_model(model, train_loader, val_loader, model_name, epochs=6, lr=0.001):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    best_state = None
    best_f1 = -1.0
    history = []

    for epoch in range(1, epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion)
        val_metrics = evaluate_model(model, val_loader, criterion)

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_metrics["loss"], 4),
            "val_accuracy": round(val_metrics["accuracy"], 4),
            "val_macro_f1": round(val_metrics["macro_f1"], 4),
        })

        if val_metrics["macro_f1"] > best_f1:
            best_f1 = val_metrics["macro_f1"]
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    return history


def cosine_similarity(a, b):
    denominator = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denominator)


def get_nearest_neighbors(model, vocab, query_word, top_k=5):
    query_word = normalize_text(query_word)

    if query_word not in vocab:
        return []

    embedding_matrix = model.embedding.weight.detach().cpu().numpy()
    query_idx = vocab[query_word]
    query_vector = embedding_matrix[query_idx]

    neighbors = []

    for word, idx in vocab.items():
        if word in {PAD_TOKEN, UNK_TOKEN, query_word}:
            continue

        similarity = cosine_similarity(query_vector, embedding_matrix[idx])
        neighbors.append((word, round(similarity, 4)))

    neighbors.sort(key=lambda item: item[1], reverse=True)

    return neighbors[:top_k]


@torch.no_grad()
def predict_with_attention(question):
    NLP_SYSTEM["attention_model"].eval()

    normalized_question = normalize_text(question)
    tokens = simple_tokenize(normalized_question)

    input_ids, length = encode_tokens(tokens, NLP_SYSTEM["vocab"], NLP_SYSTEM["max_len"])

    x = torch.tensor([input_ids], dtype=torch.long).to(DEVICE)
    l = torch.tensor([length], dtype=torch.long).to(DEVICE)

    logits, attention_weights = NLP_SYSTEM["attention_model"](x, l, return_attention=True)

    probabilities = torch.softmax(logits, dim=1).squeeze(0)
    predicted_id = int(torch.argmax(probabilities).item())

    confidence = float(probabilities[predicted_id].item())
    predicted_intent = ID2LABEL[predicted_id]

    attention_values = attention_weights.squeeze(0).cpu().numpy()[:length]

    token_attention = []
    for token, weight in zip(tokens, attention_values):
        token_attention.append({
            "token": token,
            "weight": round(float(weight), 4),
        })

    return {
        "predicted_intent": predicted_intent,
        "confidence": round(confidence, 4),
        "model_used": "Attention-BiGRU neural intent classifier",
        "attention_weights": token_attention,
    }


def check_transformer_status():
    try:
        import transformers  # noqa: F401

        return {
            "available": True,
            "model": "DistilBERT transfer-learning extension available",
            "status": "Transformers is installed. This project can be extended to use DistilBERT fine-tuning.",
        }
    except Exception:
        return {
            "available": False,
            "model": "DistilBERT transfer-learning extension",
            "status": "Transformers is not installed in this environment, so the final live demo uses the local Attention-BiGRU model.",
        }


def initialize_nlp_system():
    texts, labels = generate_training_data(n_per_intent=90)

    train_texts, temp_texts, train_labels, temp_labels = train_test_split(
        texts,
        labels,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=labels,
    )

    val_texts, test_texts, val_labels, test_labels = train_test_split(
        temp_texts,
        temp_labels,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_labels,
    )

    vocab = build_vocab(train_texts)
    max_len = 24

    train_dataset = IntentDataset(train_texts, train_labels, vocab, max_len=max_len)
    val_dataset = IntentDataset(val_texts, val_labels, vocab, max_len=max_len)
    test_dataset = IntentDataset(test_texts, test_labels, vocab, max_len=max_len)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64)
    test_loader = DataLoader(test_dataset, batch_size=64)

    gru_model = GRUIntentClassifier(
        vocab_size=len(vocab),
        embed_dim=96,
        hidden_dim=96,
        num_classes=len(INTENT_LABELS),
        pad_idx=vocab[PAD_TOKEN],
    ).to(DEVICE)

    attention_model = AttentionBiGRUIntentClassifier(
        vocab_size=len(vocab),
        embed_dim=96,
        hidden_dim=96,
        num_classes=len(INTENT_LABELS),
        pad_idx=vocab[PAD_TOKEN],
    ).to(DEVICE)

    gru_history = train_model(
        gru_model,
        train_loader,
        val_loader,
        model_name="GRU",
        epochs=5,
        lr=0.001,
    )

    attention_history = train_model(
        attention_model,
        train_loader,
        val_loader,
        model_name="Attention-BiGRU",
        epochs=5,
        lr=0.001,
    )

    criterion = nn.CrossEntropyLoss()
    gru_test_metrics = evaluate_model(gru_model, test_loader, criterion)
    attention_test_metrics = evaluate_model(attention_model, test_loader, criterion)

    return {
        "vocab": vocab,
        "max_len": max_len,
        "gru_model": gru_model,
        "attention_model": attention_model,
        "gru_history": gru_history,
        "attention_history": attention_history,
        "gru_test_metrics": {
            "accuracy": round(gru_test_metrics["accuracy"], 4),
            "macro_f1": round(gru_test_metrics["macro_f1"], 4),
            "loss": round(gru_test_metrics["loss"], 4),
        },
        "attention_test_metrics": {
            "accuracy": round(attention_test_metrics["accuracy"], 4),
            "macro_f1": round(attention_test_metrics["macro_f1"], 4),
            "loss": round(attention_test_metrics["loss"], 4),
        },
        "dataset_summary": {
            "total_examples": len(texts),
            "train_examples": len(train_texts),
            "validation_examples": len(val_texts),
            "test_examples": len(test_texts),
            "intent_labels": INTENT_LABELS,
            "vocab_size": len(vocab),
        },
        "transfer_learning": check_transformer_status(),
    }


print("Initializing neural NLP engine...")
NLP_SYSTEM = initialize_nlp_system()
print("Neural NLP engine ready.")


def predict_intent(question: str):
    prediction = predict_with_attention(question)

    embedding_neighbors = {
        "going": get_nearest_neighbors(NLP_SYSTEM["attention_model"], NLP_SYSTEM["vocab"], "going"),
        "next": get_nearest_neighbors(NLP_SYSTEM["attention_model"], NLP_SYSTEM["vocab"], "next"),
        "schedule": get_nearest_neighbors(NLP_SYSTEM["attention_model"], NLP_SYSTEM["vocab"], "schedule"),
    }

    prediction["word_representations"] = {
        "embedding_layer": "Learned neural embedding layer from the Attention-BiGRU model",
        "nearest_neighbors": embedding_neighbors,
    }

    return prediction


def get_nlp_system_status():
    return {
        "system_name": "Neural NLP System for Campus Agent Queries",
        "device": str(DEVICE),
        "implemented_components": {
            "word_representations": "Implemented with a learned embedding layer and nearest-neighbor similarity.",
            "sequence_modeling": "Implemented with a GRU intent classifier.",
            "attention_model": "Implemented with an Attention-BiGRU classifier and token attention weights.",
            "transfer_learning": NLP_SYSTEM["transfer_learning"],
            "system_analysis": "Implemented with train/validation history and test metrics.",
            "end_to_end_integration": "React sends a question and selected agent state to Flask. Flask predicts intent with the neural model and generates an answer from the campus reasoning layer.",
        },
        "dataset_summary": NLP_SYSTEM["dataset_summary"],
        "model_metrics": {
            "gru_test_metrics": NLP_SYSTEM["gru_test_metrics"],
            "attention_bigru_test_metrics": NLP_SYSTEM["attention_test_metrics"],
        },
        "training_history": {
            "gru": NLP_SYSTEM["gru_history"],
            "attention_bigru": NLP_SYSTEM["attention_history"],
        },
        "intent_labels": INTENT_LABELS,
    }