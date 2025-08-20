def sum_weights(adapt_or_not_step):
    total_weight = 0
    for key, value in adapt_or_not_step.items():
        weight = value[0]
        total_weight += weight
    return total_weight

def compare_function(adapt_or_not_step):
    sum = 0
    total_weight = sum_weights(adapt_or_not_step)
    for key, value in adapt_or_not_step.items():
        weight = value[0]  # giả sử giá trị đầu tiên là trọng số
        fraction_str = value[1]  # giả sử value[1] là '5/7' hoặc '0.8'
        if '/' in fraction_str:
            numerator, denominator = fraction_str.split('/')
            try:
                numerator = float(numerator)
                denominator = float(denominator)
                if denominator == 0:  # mẫu bằng 0
                    x = 0
                else:
                    x = numerator / denominator
            except ValueError:  # tử hoặc mẫu có chữ (không phải số)
                x = 0
        else:
            try:
                x = float(fraction_str)  # nếu là số thập phân
            except ValueError:
                x = 0
        weight = float(weight)
        sum += x * weight / total_weight
    return sum

def merge_dicts(kha_nang_dap_ung_tham_chieu_step, context_queries):
    for k, v in kha_nang_dap_ung_tham_chieu_step.items():
        if k in context_queries and isinstance(v, dict) and isinstance(context_queries[k], dict):
            # Nếu cả 2 cùng là dict thì merge đệ quy
            merge_dicts(v, context_queries[k])
        else:
            # Nếu không phải dict hoặc key chưa tồn tại trong B thì gán trực tiếp
            context_queries[k] = v
    return context_queries