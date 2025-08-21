def sum_weights(adapt_or_not_step):
    """
    Tính tổng weight - bây giờ weight là số item đáp ứng
    """
    total_weight = 0
    for key, value in adapt_or_not_step.items():
        weight = value[0]  # weight = số item đáp ứng
        total_weight += weight
    return total_weight

def compare_function(adapt_or_not_step):
    """
    So sánh và tính điểm tổng thể dựa trên từng item đáp ứng
    Weight bây giờ là số item đáp ứng (những item có adapt_or_not = "1")
    """
    sum_score = 0
    total_weight = sum_weights(adapt_or_not_step)
    
    if total_weight == 0:
        return 0  # Không có item nào đáp ứng
    
    for key, value in adapt_or_not_step.items():
        weight = value[0]  # số item đáp ứng trong requirement này
        fraction_str = value[1]  # tỷ lệ như '3/5'
        
        # Parse fraction
        if '/' in fraction_str:
            try:
                numerator, denominator = fraction_str.split('/')
                numerator = float(numerator)
                denominator = float(denominator)
                if denominator == 0:
                    ratio = 0
                else:
                    ratio = numerator / denominator
            except ValueError:
                ratio = 0
        else:
            try:
                ratio = float(fraction_str)
            except ValueError:
                ratio = 0
        
        # Tính điểm có trọng số
        weight = float(weight)
        sum_score += ratio * weight / total_weight
    
    return sum_score

def merge_dicts(kha_nang_dap_ung_tham_chieu_step, context_queries):
    """
    Merge dữ liệu từ kha_nang_dap_ung_tham_chieu_step vào context_queries
    Bao gồm cả trường adapt_or_not mới
    """
    for k, v in kha_nang_dap_ung_tham_chieu_step.items():
        if k in context_queries and isinstance(v, dict) and isinstance(context_queries[k], dict):
            # Nếu cả 2 cùng là dict thì merge đệ quy
            # Đặc biệt xử lý các trường mới
            for sub_key, sub_value in v.items():
                context_queries[k][sub_key] = sub_value
        else:
            # Nếu không phải dict hoặc key chưa tồn tại trong context_queries thì gán trực tiếp
            context_queries[k] = v
    return context_queries