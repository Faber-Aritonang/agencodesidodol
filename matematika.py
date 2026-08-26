def faktorial(n):
    """Menghitung faktorial dari n.
    
    Args:
        n: Bilangan bulat non-negatif.
        
    Returns:
        Faktorial dari n.
        
    Raises:
        ValueError: Jika n negatif.
        TypeError: Jika n bukan bilangan bulat.
    """
    if not isinstance(n, int):
        raise TypeError("Input harus bilangan bulat")
    if n < 0:
        raise ValueError("Input tidak boleh negatif")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
